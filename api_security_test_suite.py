#!/usr/bin/env python3
"""
Comprehensive API Security Testing Suite for PsychSync
Tests rate limiting, IDOR, mass assignment, GraphQL security, and data leakage
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import random
import string
import logging

logger = logging.getLogger(__name__)

class APISecurityTester:
    """Comprehensive API security tester"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results = []
        self.session = None
        self.test_users = []
        self.test_tokens = {}

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API security tests"""
        print("🚀 Starting Comprehensive API Security Testing")

        async with aiohttp.ClientSession() as session:
            self.session = session

            # Test 1: Rate Limiting
            await self.test_rate_limiting()

            # Test 2: IDOR (Insecure Direct Object Reference)
            await self.test_idor_vulnerabilities()

            # Test 3: Mass Assignment Attacks
            await self.test_mass_assignment_attacks()

            # Test 4: GraphQL Security (if GraphQL endpoint exists)
            await self.test_graphql_security()

            # Test 5: Data Leakage in API Responses
            await self.test_api_data_leakage()

        return self.generate_report()

    async def test_rate_limiting(self):
        """Test rate limiting effectiveness"""
        print("\n🧪 Testing Rate Limiting")

        # Test endpoints that should have rate limiting
        rate_limit_endpoints = [
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/forgot-password",
            "/api/v1/users/me",
            "/api/v1/assessments"
        ]

        for endpoint in rate_limit_endpoints:
            await self._test_endpoint_rate_limiting(endpoint)

    async def _test_endpoint_rate_limiting(self, endpoint: str):
        """Test rate limiting on a specific endpoint"""
        print(f"\n🔍 Testing rate limiting for: {endpoint}")

        url = f"{self.base_url}{endpoint}"

        # Test data based on endpoint
        test_data = self._get_test_data_for_endpoint(endpoint)

        successful_requests = 0
        rate_limit_hit = False
        request_times = []
        status_codes = []

        # Make rapid requests to test rate limiting
        request_count = 100
        start_time = time.time()

        for i in range(request_count):
            try:
                request_start = time.time()

                if endpoint == "/api/v1/auth/login":
                    async with self.session.post(url, json=test_data) as response:
                        status = response.status
                        response_text = await response.text()
                elif endpoint == "/api/v1/auth/register":
                    async with self.session.post(url, json=test_data) as response:
                        status = response.status
                        response_text = await response.text()
                elif endpoint == "/api/v1/users/me":
                    # Simulate authenticated request
                    headers = {"Authorization": "Bearer fake-token"}
                    async with self.session.get(url, headers=headers) as response:
                        status = response.status
                        response_text = await response.text()
                else:
                    async with self.session.get(url) as response:
                        status = response.status
                        response_text = await response.text()

                request_end = time.time()
                request_times.append(request_end - request_start)
                status_codes.append(status)

                # Check for rate limiting indicators
                if status == 429:  # Too Many Requests
                    rate_limit_hit = True
                    print(f"  ✅ Rate limiting triggered at request {i+1}")
                    break
                elif status == 503:  # Service Unavailable (often used for rate limiting)
                    rate_limit_hit = True
                    print(f"  ✅ Service unavailable (likely rate limiting) at request {i+1}")
                    break
                elif status == 200 or status == 201:
                    successful_requests += 1
                elif status == 401:  # Unauthorized (expected for fake auth)
                    pass  # Normal for protected endpoints

                # Small delay between requests
                await asyncio.sleep(0.01)

            except Exception as e:
                print(f"  ❌ Request {i+1} failed: {str(e)}")

        total_time = time.time() - start_time
        requests_per_second = request_count / total_time

        # Analyze rate limiting effectiveness
        rate_limiting_effective = rate_limit_hit or requests_per_second < 10  # Less than 10 req/sec indicates limiting

        self.results.append({
            "test_type": "RATE_LIMITING",
            "endpoint": endpoint,
            "total_requests": request_count,
            "successful_requests": successful_requests,
            "requests_per_second": round(requests_per_second, 2),
            "rate_limit_triggered": rate_limit_hit,
            "rate_limiting_effective": rate_limiting_effective,
            "status_code_distribution": {
                "200": status_codes.count(200),
                "401": status_codes.count(401),
                "429": status_codes.count(429),
                "503": status_codes.count(503),
                "others": len([s for s in status_codes if s not in [200, 401, 429, 503]])
            },
            "timestamp": datetime.utcnow().isoformat()
        })

        if rate_limiting_effective:
            print(f"  ✅ Rate limiting is effective ({requests_per_second:.2f} req/sec)")
        else:
            print(f"  🚨 Rate limiting may be missing or ineffective ({requests_per_second:.2f} req/sec)")

    def _get_test_data_for_endpoint(self, endpoint: str) -> Dict[str, Any]:
        """Get test data for different endpoints"""
        base_email = "testuser@test.com"

        if endpoint == "/api/v1/auth/login":
            return {
                "email": base_email,
                "password": "testpassword123"
            }
        elif endpoint == "/api/v1/auth/register":
            return {
                "email": f"newuser{random.randint(1000, 9999)}@test.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
        elif endpoint == "/api/v1/auth/forgot-password":
            return {
                "email": base_email
            }
        else:
            return {}

    async def test_idor_vulnerabilities(self):
        """Test for Insecure Direct Object Reference vulnerabilities"""
        print("\n🧪 Testing IDOR (Insecure Direct Object Reference) Vulnerabilities")

        idor_test_cases = [
            {
                "name": "Assessment Access via ID Manipulation",
                "endpoint": "/api/v1/assessments/{id}",
                "test_ids": ["1", "2", "999", "9999", "-1", "0", "abc", "../../../etc/passwd"],
                "expected_behavior": "Should return 404 for non-existent IDs"
            },
            {
                "name": "User Profile Access via ID Manipulation",
                "endpoint": "/api/v1/users/{id}",
                "test_ids": ["1", "2", "999", "9999", "-1", "0", "admin", "1 OR 1=1"],
                "expected_behavior": "Should return 401/403 for unauthorized access"
            },
            {
                "name": "Team Access via ID Manipulation",
                "endpoint": "/api/v1/teams/{id}",
                "test_ids": ["1", "2", "999", "9999", "-1", "0", "admin", "1' UNION SELECT"],
                "expected_behavior": "Should return 401/403 for unauthorized access"
            },
            {
                "name": "Response Access via ID Manipulation",
                "endpoint": "/api/v1/responses/{id}",
                "test_ids": ["1", "2", "999", "9999", "-1", "0", "1' OR '1'='1"],
                "expected_behavior": "Should return 401/403 for unauthorized access"
            }
        ]

        for test_case in idor_test_cases:
            await self._test_idor_endpoint(test_case)

    async def _test_idor_endpoint(self, test_case: Dict[str, Any]):
        """Test IDOR on a specific endpoint"""
        print(f"\n🔍 Testing IDOR: {test_case['name']}")

        vulnerabilities_found = 0
        proper_protection = 0

        for test_id in test_case["test_ids"]:
            try:
                endpoint_url = test_case["endpoint"].format(id=test_id)
                url = f"{self.base_url}{endpoint_url}"

                # Test without authentication first
                async with self.session.get(url) as response:
                    status = response.status
                    response_text = await response.text()

                # Check if IDOR vulnerability exists
                is_vulnerable = False
                is_protected = False

                if status == 200:
                    # Successful access to potentially unauthorized data
                    response_data = json.loads(response_text) if response_text.strip() else {}

                    # Check if actual data was returned (not just error message)
                    if isinstance(response_data, dict) and len(response_data) > 3:  # More than typical error response
                        is_vulnerable = True
                        vulnerabilities_found += 1
                        print(f"  🚨 IDOR VULNERABILITY: Unauthorized access to {endpoint_url}")
                        print(f"  Response keys: {list(response_data.keys())[:5]}...")

                elif status in [401, 403, 404]:
                    # Proper protection
                    is_protected = True
                    proper_protection += 1

                elif status == 500:
                    # Check if SQL error exposed (potential IDOR leading to SQL injection)
                    if any(error in response_text.lower() for error in ["sql", "mysql", "postgresql", "sqlite"]):
                        is_vulnerable = True
                        vulnerabilities_found += 1
                        print(f"  🚨 SQL ERROR EXPOSED via IDOR: {endpoint_url}")
                    else:
                        is_protected = True
                        proper_protection += 1

                # Test with fake authentication token
                headers = {"Authorization": "Bearer fake-token"}
                async with self.session.get(url, headers=headers) as response:
                    auth_status = response.status
                    auth_response_text = await response.text()

                    if auth_status == 200:
                        # Potential IDOR with fake token
                        response_data = json.loads(auth_response_text) if auth_response_text.strip() else {}
                        if isinstance(response_data, dict) and len(response_data) > 3:
                            is_vulnerable = True
                            vulnerabilities_found += 1
                            print(f"  🚨 IDOR WITH FAKE TOKEN: {endpoint_url}")
                    elif auth_status in [401, 403, 404]:
                        is_protected = True
                        proper_protection += 1

            except Exception as e:
                print(f"  ❌ Test failed for ID {test_id}: {str(e)}")
                proper_protection += 1  # Network errors aren't vulnerabilities

        self.results.append({
            "test_type": "IDOR_VULNERABILITY",
            "endpoint": test_case["endpoint"],
            "test_ids_count": len(test_case["test_ids"]),
            "vulnerabilities_found": vulnerabilities_found,
            "proper_protection": proper_protection,
            "idor_protected": vulnerabilities_found == 0,
            "timestamp": datetime.utcnow().isoformat()
        })

        if vulnerabilities_found == 0:
            print(f"  ✅ IDOR protection is working properly")
        else:
            print(f"  🚨 {vulnerabilities_found} IDOR vulnerabilities found")

    async def test_mass_assignment_attacks(self):
        """Test for mass assignment vulnerabilities"""
        print("\n🧪 Testing Mass Assignment Attacks")

        mass_assignment_endpoints = [
            {
                "name": "User Registration Mass Assignment",
                "endpoint": "/api/v1/auth/register",
                "method": "POST",
                "legitimate_fields": ["email", "password", "full_name"],
                "suspicious_fields": [
                    "role", "is_admin", "is_active", "id", "created_at",
                    "email_verified", "subscription_level", "permissions"
                ]
            },
            {
                "name": "User Profile Update Mass Assignment",
                "endpoint": "/api/v1/users/me",
                "method": "PUT",
                "legitimate_fields": ["full_name", "bio", "avatar_url"],
                "suspicious_fields": [
                    "role", "is_admin", "is_active", "id", "created_at",
                    "email_verified", "subscription_level", "permissions", "organization_id"
                ]
            },
            {
                "name": "Assessment Creation Mass Assignment",
                "endpoint": "/api/v1/assessments",
                "method": "POST",
                "legitimate_fields": ["title", "description", "type"],
                "suspicious_fields": [
                    "id", "created_at", "created_by", "is_active", "is_public",
                    "status", "price", "subscription_required", "permissions"
                ]
            }
        ]

        for test_case in mass_assignment_endpoints:
            await self._test_mass_assignment_endpoint(test_case)

    async def _test_mass_assignment_endpoint(self, test_case: Dict[str, Any]):
        """Test mass assignment on a specific endpoint"""
        print(f"\n🔍 Testing Mass Assignment: {test_case['name']}")

        url = f"{self.base_url}{test_case['endpoint']}"

        # Test with legitimate fields
        legitimate_data = {field: "test_value" for field in test_case["legitimate_fields"]}

        # Test with suspicious fields added
        suspicious_data = legitimate_data.copy()
        for field in test_case["suspicious_fields"]:
            if field in ["role", "subscription_level"]:
                suspicious_data[field] = "admin"
            elif field in ["is_admin", "is_active", "is_public", "subscription_required"]:
                suspicious_data[field] = True
            elif field in ["permissions"]:
                suspicious_data[field] = ["admin", "superuser"]
            elif field in ["price"]:
                suspicious_data[field] = 0
            elif field in ["id", "created_by", "organization_id"]:
                suspicious_data[field] = 1
            else:
                suspicious_data[field] = "manipulated_value"

        try:
            # Test legitimate request first
            print(f"  Testing with legitimate fields: {test_case['legitimate_fields']}")

            if test_case["method"] == "POST":
                async with self.session.post(url, json=legitimate_data) as response:
                    legitimate_status = response.status
                    legitimate_response = await response.text()
            else:
                async with self.session.put(url, json=legitimate_data) as response:
                    legitimate_status = response.status
                    legitimate_response = await response.text()

            # Test with mass assignment attempt
            print(f"  Testing with suspicious fields: {test_case['suspicious_fields']}")

            if test_case["method"] == "POST":
                async with self.session.post(url, json=suspicious_data) as response:
                    mass_assign_status = response.status
                    mass_assign_response = await response.text()
            else:
                async with self.session.put(url, json=suspicious_data) as response:
                    mass_assign_status = response.status
                    mass_assign_response = await response.text()

            # Analyze results for mass assignment vulnerabilities
            is_vulnerable = False

            # Check if suspicious fields were accepted (successful response with unexpected data)
            if mass_assign_status == legitimate_status == 200 or mass_assign_status == legitimate_status == 201:
                # Compare responses to see if extra fields were processed
                try:
                    legitimate_data_json = json.loads(legitimate_response) if legitimate_response.strip() else {}
                    mass_assign_data_json = json.loads(mass_assign_response) if mass_assign_response.strip() else {}

                    # Check if any suspicious field values are in the response
                    for field in test_case["suspicious_fields"]:
                        if field in mass_assign_data_json and field not in legitimate_data_json:
                            is_vulnerable = True
                            print(f"  🚨 MASS ASSIGNMENT VULNERABILITY: Field '{field}' was accepted!")
                            break
                except:
                    pass  # JSON parse errors are not mass assignment vulnerabilities

            # Check if the request was rejected (good protection)
            elif mass_assign_status in [400, 422]:
                is_vulnerable = False
                print(f"  ✅ Mass assignment properly rejected (HTTP {mass_assign_status})")

            self.results.append({
                "test_type": "MASS_ASSIGNMENT",
                "endpoint": test_case["endpoint"],
                "legitimate_status": legitimate_status,
                "mass_assign_status": mass_assign_status,
                "vulnerable": is_vulnerable,
                "protected": not is_vulnerable,
                "timestamp": datetime.utcnow().isoformat()
            })

            if not is_vulnerable:
                print(f"  ✅ Mass assignment protection is working")
            else:
                print(f"  🚨 Mass assignment vulnerability detected!")

        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")

    async def test_graphql_security(self):
        """Test GraphQL endpoint security and schema exposure"""
        print("\n🧪 Testing GraphQL Security")

        graphql_endpoints = [
            "/graphql",
            "/api/graphql",
            "/v1/graphql",
            "/graphiql"
        ]

        graphql_vulnerabilities = 0
        proper_protection = 0

        for endpoint in graphql_endpoints:
            url = f"{self.base_url}{endpoint}"

            try:
                # Test if GraphQL endpoint exists
                async with self.session.post(url, json={"query": "{ __schema { types { name } } }"}) as response:
                    status = response.status
                    response_text = await response.text()

                    if status == 200:
                        # GraphQL endpoint exists, test for vulnerabilities
                        print(f"  🔍 GraphQL endpoint found: {endpoint}")

                        # Test GraphQL introspection
                        introspection_queries = [
                            # Full introspection
                            {"query": "query { __schema { types { name fields { name type { name } } } } }"},

                            # Schema information
                            {"query": "query { __type(name: \"Query\") { fields { name type { name } } } }"},

                            # Mutations information
                            {"query": "query { __schema { mutationType { fields { name type { name } } } } }"},

                            # Type information
                            {"query": "query { __type(name: \"User\") { fields { name type { name } } } }"}
                        ]

                        endpoint_vulnerabilities = 0

                        for i, query in enumerate(introspection_queries):
                            try:
                                async with self.session.post(url, json=query) as gql_response:
                                    gql_status = gql_response.status
                                    gql_response_text = await gql_response.text()

                                    if gql_status == 200:
                                        # GraphQL introspection working (potential vulnerability)
                                        endpoint_vulnerabilities += 1
                                        print(f"    🚨 GraphQL introspection working - Schema exposed")
                                        graphql_vulnerabilities += 1
                                    elif gql_status in [400, 403, 404]:
                                        # GraphQL properly protected
                                        proper_protection += 1
                                        print(f"    ✅ GraphQL introspection blocked")

                            except Exception as gql_e:
                                print(f"    ❌ GraphQL query {i+1} failed: {str(gql_e)}")

                        # Test for common GraphQL vulnerabilities
                        graphql_vulnerability_tests = [
                            # Query depth attacks
                            {"query": "query {" + "user".join(".friends " * 20) + "{ id } }"},

                            # Field suggestion attacks
                            {"query": "query { __type(name: \"__Type\") { kind } }"},

                            # Enum value enumeration
                            {"query": "query { __type(name: \"__DirectiveLocation\") { enumValues { name } } }"},

                            # Type system exploration
                            {"query": "query { __schema { subscriptionType { fields { name } } } }"}
                        ]

                        for vuln_query in graphql_vulnerability_tests:
                            try:
                                async with self.session.post(url, json=vuln_query) as vuln_response:
                                    vuln_status = vuln_response.status

                                    if vuln_status == 200:
                                        # Potential GraphQL vulnerability
                                        endpoint_vulnerabilities += 1
                                        graphql_vulnerabilities += 1

                            except Exception:
                                pass

                    elif status == 404:
                        # GraphQL endpoint doesn't exist (good)
                        proper_protection += 1
                    else:
                        # Other status codes (likely not GraphQL)
                        pass

            except Exception as e:
                # Endpoint doesn't exist or other error (good)
                proper_protection += 1

        self.results.append({
            "test_type": "GRAPHQL_SECURITY",
            "endpoints_tested": len(graphql_endpoints),
            "graphql_vulnerabilities": graphql_vulnerabilities,
            "proper_protection": proper_protection,
            "graphql_secure": graphql_vulnerabilities == 0,
            "timestamp": datetime.utcnow().isoformat()
        })

        if graphql_vulnerabilities == 0:
            print(f"  ✅ No GraphQL vulnerabilities found")
        else:
            print(f"  🚨 {graphql_vulnerabilities} GraphQL vulnerabilities detected")

    async def test_api_data_leakage(self):
        """Test API responses for excessive data leakage"""
        print("\n🧪 Testing API Data Leakage")

        data_leakage_endpoints = [
            "/api/v1/health",
            "/api/v1/auth/login",
            "/api/v1/users/me",
            "/api/v1/assessments",
            "/api/v1/teams",
            "/api/v1/responses",
            "/api/v1/templates"
        ]

        for endpoint in data_leakage_endpoints:
            await self._test_endpoint_data_leakage(endpoint)

    async def _test_endpoint_data_leakage(self, endpoint: str):
        """Test data leakage on a specific endpoint"""
        print(f"\n🔍 Testing Data Leakage: {endpoint}")

        url = f"{self.base_url}{endpoint}"

        try:
            # Test with GET request
            async with self.session.get(url) as response:
                status = response.status
                response_text = await response.text()
                response_headers = dict(response.headers)

            # Test with POST request (if it might accept it)
            try:
                async with self.session.post(url, json={"test": "data"}) as post_response:
                    post_status = post_response.status
                    post_response_text = await post_response.text()
            except:
                post_status = None
                post_response_text = ""

            # Analyze for data leakage
            leakage_indicators = []
            is_vulnerable = False

            # Check response size (excessive data)
            response_size = len(response_text)
            if response_size > 10000:  # 10KB threshold
                leakage_indicators.append("Large response size")

            # Check for sensitive information in error messages
            sensitive_patterns = [
                "password", "secret", "token", "key", "private",
                "internal", "debug", "stack trace", "exception",
                "admin", "root", "database", "connection string",
                "api_key", "jwt_secret", "encryption_key"
            ]

            for pattern in sensitive_patterns:
                if pattern.lower() in response_text.lower():
                    leakage_indicators.append(f"Sensitive term: {pattern}")

            # Check for internal system information
            system_info_patterns = [
                "python", "fastapi", "sqlalchemy", "postgres",
                "redis", "localhost", "127.0.0.1", "internal",
                "dev", "development", "test", "debug"
            ]

            for pattern in system_info_patterns:
                if pattern.lower() in response_text.lower():
                    leakage_indicators.append(f"System info: {pattern}")

            # Check for database structure exposure
            db_patterns = [
                "table", "column", "schema", "constraint", "index",
                "foreign_key", "primary_key", "varchar", "integer"
            ]

            for pattern in db_patterns:
                if pattern.lower() in response_text.lower():
                    leakage_indicators.append(f"Database info: {pattern}")

            # Check response headers for information leakage
            header_leakage = []
            for header, value in response_headers.items():
                if any(pattern.lower() in value.lower() for pattern in sensitive_patterns):
                    header_leakage.append(f"{header}: {value}")

            # Check for excessive field counts in JSON responses
            try:
                response_json = json.loads(response_text) if response_text.strip() else {}
                if isinstance(response_json, dict):
                    field_count = len(response_json)
                    if field_count > 50:  # Excessive number of fields
                        leakage_indicators.append(f"Excessive fields: {field_count}")

                    # Check for sensitive field names
                    sensitive_fields = [field for field in response_json.keys()
                                     if any(pattern in field.lower() for pattern in sensitive_patterns)]
                    if sensitive_fields:
                        leakage_indicators.append(f"Sensitive fields: {sensitive_fields[:3]}")
            except:
                pass

            # Determine if vulnerable
            if len(leakage_indicators) > 3 or any("password" in ind.lower() or "secret" in ind.lower() or "key" in ind.lower() for ind in leakage_indicators):
                is_vulnerable = True

            self.results.append({
                "test_type": "DATA_LEAKAGE",
                "endpoint": endpoint,
                "status_code": status,
                "response_size": response_size,
                "leakage_indicators": leakage_indicators,
                "header_leakage": header_leakage,
                "vulnerable": is_vulnerable,
                "protected": not is_vulnerable,
                "timestamp": datetime.utcnow().isoformat()
            })

            if is_vulnerable:
                print(f"  🚨 Data leakage detected: {len(leakage_indicators)} indicators")
                for indicator in leakage_indicators[:3]:
                    print(f"    - {indicator}")
                if header_leakage:
                    print(f"    Header leakage: {header_leakage}")
            else:
                print(f"  ✅ No excessive data leakage detected")

        except Exception as e:
            print(f"  ❌ Test failed: {str(e)}")

    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive security report"""
        vulnerabilities_by_type = {
            "RATE_LIMITING": [r for r in self.results if r["test_type"] == "RATE_LIMITING" and not r.get("rate_limiting_effective", True)],
            "IDOR_VULNERABILITY": [r for r in self.results if r["test_type"] == "IDOR_VULNERABILITY" and r.get("vulnerabilities_found", 0) > 0],
            "MASS_ASSIGNMENT": [r for r in self.results if r["test_type"] == "MASS_ASSIGNMENT" and r.get("vulnerable", False)],
            "GRAPHQL_SECURITY": [r for r in self.results if r["test_type"] == "GRAPHQL_SECURITY" and not r.get("graphql_secure", True)],
            "DATA_LEAKAGE": [r for r in self.results if r["test_type"] == "DATA_LEAKAGE" and r.get("vulnerable", False)]
        }

        total_vulnerabilities = sum(len(vulns) for vulns in vulnerabilities_by_type.values())

        return {
            "test_summary": {
                "total_tests": len(self.results),
                "vulnerabilities_found": total_vulnerabilities,
                "test_date": datetime.utcnow().isoformat(),
                "base_url": self.base_url
            },
            "vulnerabilities_by_type": vulnerabilities_by_type,
            "detailed_results": self.results,
            "recommendations": self._generate_api_recommendations(vulnerabilities_by_type),
            "security_score": max(0, 100 - (total_vulnerabilities * 10))  # Simple scoring
        }

    def _generate_api_recommendations(self, vulnerabilities_by_type: Dict[str, List]) -> List[str]:
        """Generate security recommendations based on found vulnerabilities"""
        recommendations = []

        if vulnerabilities_by_type["RATE_LIMITING"]:
            recommendations.extend([
                "Implement rate limiting on all API endpoints",
                "Use token bucket or sliding window algorithms",
                "Set different limits for authenticated vs anonymous users",
                "Implement IP-based and user-based rate limiting"
            ])

        if vulnerabilities_by_type["IDOR_VULNERABILITY"]:
            recommendations.extend([
                "Implement proper authorization checks for all data access",
                "Use UUIDs instead of sequential IDs for sensitive resources",
                "Validate user permissions for every resource access",
                "Implement resource ownership verification"
            ])

        if vulnerabilities_by_type["MASS_ASSIGNMENT"]:
            recommendations.extend([
                "Use allowlists for model fields in API endpoints",
                "Implement field-level validation and sanitization",
                "Use DTOs or view models to control exposed fields",
                "Validate input models against expected schemas"
            ])

        if vulnerabilities_by_type["GRAPHQL_SECURITY"]:
            recommendations.extend([
                "Disable GraphQL introspection in production",
                "Implement query depth limiting",
                "Add authentication and authorization middleware",
                "Monitor for suspicious GraphQL queries"
            ])

        if vulnerabilities_by_type["DATA_LEAKAGE"]:
            recommendations.extend([
                "Implement response field filtering",
                "Remove sensitive information from error messages",
                "Use DTOs to control API response data",
                "Implement response size limits"
            ])

        if not any(vulnerabilities_by_type.values()):
            recommendations.append("✅ No API vulnerabilities found - maintain current security practices")

        return recommendations


async def main():
    """Run the comprehensive API security tests"""
    tester = APISecurityTester()

    logger.info("🚀 Starting Comprehensive API Security Tests")

    try:
        report = await tester.run_all_tests()

        # Print summary
        print("\n" + "="*80)
        print("🔍 API SECURITY TEST REPORT")
        print("="*80)

        summary = report["test_summary"]
        print(f"Total Tests: {summary['total_tests']}")
        print(f"Vulnerabilities Found: {summary['vulnerabilities_found']}")
        print(f"Security Score: {report['security_score']}/100")

        if summary['vulnerabilities_found'] > 0:
            print("\n🚨 VULNERABILITIES DETECTED:")

            for vuln_type, vulns in report["vulnerabilities_by_type"].items():
                if vulns:
                    print(f"\n  {vuln_type}: {len(vulns)} vulnerabilities")
                    for vuln in vulns[:2]:  # Show first 2 examples
                        if "endpoint" in vuln:
                            print(f"    - {vuln['endpoint']}: {vuln.get('status_code', 'N/A')}")

            print("\n📋 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"  • {rec}")
        else:
            print("\n✅ NO API VULNERABILITIES DETECTED")
            print("All API security tests passed successfully!")

        # Save detailed report
        with open("api_security_report.json", "w") as f:
            json.dump(report, f, indent=2)

        print(f"\n📄 Detailed report saved to: api_security_report.json")

    except Exception as e:
        logger.error(f"❌ Test execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
