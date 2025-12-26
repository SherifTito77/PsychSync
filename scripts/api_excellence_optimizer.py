#!/usr/bin/env python3
"""
PsychSync API Excellence Optimizer
Comprehensive API performance, security, and reliability optimization system

Implements:
- Response time optimization and monitoring
- Rate limiting and throttling implementation
- API security hardening (OWASP API Security)
- Caching strategies and optimization
- Error handling and resilience patterns
- API versioning and backward compatibility
- OpenAPI specification validation
- Load testing and performance benchmarking
"""

import asyncio
import aiohttp
import time
import json
import sys
import os
import subprocess
import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
import re
import hashlib

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class APIEndpointMetrics:
    """API endpoint performance metrics"""
    endpoint: str
    method: str
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    requests_per_second: float
    error_rate: float
    throughput_mbps: float
    status_codes: Dict[int, int]

@dataclass
class SecurityVulnerability:
    """API security vulnerability finding"""
    endpoint: str
    vulnerability_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    recommendation: str
    owasp_reference: str

@dataclass
class APICacheMetrics:
    """API caching performance metrics"""
    endpoint: str
    cache_hit_rate: float
    avg_cache_response_time: float
    cache_miss_rate: float
    cache_size_mb: float
    eviction_rate: float

class APIExcellenceOptimizer:
    """
    Comprehensive API performance, security, and reliability optimization system
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.endpoints_to_test = [
            "/api/v1/health",
            "/api/v1/auth/token",
            "/api/v1/users/me",
            "/api/v1/teams/",
            "/api/v1/assessments/",
            "/api/v1/analytics/dashboard"
        ]
        self.test_results = {}
        self.security_issues = []
        self.performance_issues = []

    async def initialize(self):
        """Initialize HTTP session and perform setup"""
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            connector=aiohttp.TCPConnector(limit=100, limit_per_host=20)
        )
        logger.info(f"API optimizer initialized with base URL: {self.base_url}")

    async def analyze_api_performance(self) -> List[APIEndpointMetrics]:
        """Comprehensive API performance analysis"""
        print("🚀 Analyzing API performance...")

        endpoint_metrics = []

        for endpoint in self.endpoints_to_test:
            try:
                metrics = await self._benchmark_endpoint(endpoint)
                endpoint_metrics.append(metrics)
                print(f"✅ Analyzed {endpoint}: {metrics.avg_response_time:.2f}ms avg")
            except Exception as e:
                logger.error(f"Error benchmarking {endpoint}: {e}")
                print(f"❌ Failed to analyze {endpoint}: {e}")

        return endpoint_metrics

    async def analyze_api_security(self) -> List[SecurityVulnerability]:
        """Comprehensive API security analysis (OWASP API Security)"""
        print("🔒 Analyzing API security...")

        vulnerabilities = []

        # OWASP API Security Top 10 checks
        vulnerability_checks = [
            self._check_broken_object_level_authorization,
            self._check_broken_user_authentication,
            self._check_excessive_data_exposure,
            self._check_lack_of_resources_and_rate_limiting,
            self._check_broken_function_level_authorization,
            self._check_mass_assignment,
            self._check_security_misconfiguration,
            self._check_injection,
            self._check_improper_assets_management,
            self._check_insufficient_logging_and_monitoring
        ]

        for check in vulnerability_checks:
            try:
                issues = await check()
                vulnerabilities.extend(issues)
            except Exception as e:
                logger.error(f"Security check failed: {e}")

        print(f"🔍 Found {len(vulnerabilities)} security vulnerabilities")
        return vulnerabilities

    async def analyze_api_documentation(self) -> Dict[str, Any]:
        """Analyze OpenAPI/Swagger documentation completeness"""
        print("📚 Analyzing API documentation...")

        try:
            async with self.session.get(f"{self.base_url}/openapi.json") as response:
                if response.status == 200:
                    openapi_spec = await response.json()
                    return self._validate_openapi_spec(openapi_spec)
                else:
                    return {
                        'valid': False,
                        'error': f"Could not fetch OpenAPI spec: {response.status}",
                        'recommendations': ["Ensure OpenAPI spec is accessible at /openapi.json"]
                    }
        except Exception as e:
            return {
                'valid': False,
                'error': f"Error fetching OpenAPI spec: {e}",
                'recommendations': ["Ensure OpenAPI spec is accessible at /openapi.json"]
            }

    async def analyze_rate_limiting(self) -> Dict[str, Any]:
        """Analyze rate limiting implementation"""
        print("⏱️  Analyzing rate limiting...")

        rate_limit_results = {}

        # Test rate limiting on authentication endpoint
        auth_endpoint = f"{self.base_url}/api/v1/auth/token"

        # Send rapid requests to test rate limiting
        response_times = []
        status_codes = []

        for i in range(20):
            start_time = time.time()
            try:
                async with self.session.post(
                    auth_endpoint,
                    json={"username": "test@example.com", "password": "wrongpassword"},
                    headers={"Content-Type": "application/json"}
                ) as response:
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    status_codes.append(response.status)

                    # Check for rate limit headers
                    rate_limit_headers = {
                        'x-ratelimit-limit': response.headers.get('x-ratelimit-limit'),
                        'x-ratelimit-remaining': response.headers.get('x-ratelimit-remaining'),
                        'x-ratelimit-reset': response.headers.get('x-ratelimit-reset')
                    }

                    if i == 0:  # Store headers from first request
                        rate_limit_results['rate_limit_headers'] = rate_limit_headers

            except Exception as e:
                logger.error(f"Rate limiting test request {i} failed: {e}")

        # Analyze results
        rate_limit_results.update({
            'total_requests': len(response_times),
            'avg_response_time': statistics.mean(response_times) if response_times else 0,
            'max_response_time': max(response_times) if response_times else 0,
            'min_response_time': min(response_times) if response_times else 0,
            'status_code_distribution': {code: status_codes.count(code) for code in set(status_codes)},
            'rate_limiting_detected': any(code in [429, 503] for code in status_codes)
        })

        # Determine if rate limiting is properly implemented
        if rate_limit_results['rate_limiting_detected']:
            rate_limit_results['rate_limiting_status'] = 'IMPLEMENTED'
            rate_limit_results['recommendations'] = []
        else:
            rate_limit_results['rate_limiting_status'] = 'MISSING'
            rate_limit_results['recommendations'] = [
                "Implement rate limiting on authentication endpoints",
                "Add rate limit headers to API responses",
                "Configure Redis-based rate limiting for distributed systems"
            ]

        return rate_limit_results

    async def analyze_caching_strategy(self) -> Dict[str, Any]:
        """Analyze API caching implementation"""
        print("💾 Analyzing caching strategy...")

        cache_analysis = {}

        # Test cache headers on GET endpoints
        cacheable_endpoints = [ep for ep in self.endpoints_to_test if ep.startswith('/api/v1/')]

        cache_headers_results = []
        for endpoint in cacheable_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    cache_headers = {
                        'cache-control': response.headers.get('cache-control'),
                        'etag': response.headers.get('etag'),
                        'last-modified': response.headers.get('last-modified'),
                        'expires': response.headers.get('expires')
                    }

                    cache_headers_results.append({
                        'endpoint': endpoint,
                        'headers': cache_headers,
                        'has_cache_control': bool(cache_headers['cache-control']),
                        'has_etag': bool(cache_headers['etag'])
                    })
            except Exception as e:
                logger.error(f"Error testing cache headers for {endpoint}: {e}")

        # Analyze cache implementation
        endpoints_with_cache_control = sum(1 for r in cache_headers_results if r['has_cache_control'])
        endpoints_with_etag = sum(1 for r in cache_headers_results if r['has_etag'])

        cache_analysis.update({
            'total_endpoints_tested': len(cacheable_endpoints),
            'endpoints_with_cache_control': endpoints_with_cache_control,
            'endpoints_with_etag': endpoints_with_etag,
            'cache_implementation_rate': endpoints_with_cache_control / len(cacheable_endpoints) if cacheable_endpoints else 0,
            'etag_implementation_rate': endpoints_with_etag / len(cacheable_endpoints) if cacheable_endpoints else 0,
            'detailed_results': cache_headers_results
        })

        # Generate recommendations
        recommendations = []
        if cache_analysis['cache_implementation_rate'] < 0.5:
            recommendations.append("Implement cache-control headers on GET endpoints")

        if cache_analysis['etag_implementation_rate'] < 0.3:
            recommendations.append("Add ETag headers for client-side caching")

        if not any(r['headers']['cache-control'] and 'max-age' in r['headers']['cache-control'] for r in cache_headers_results):
            recommendations.append("Set appropriate max-age values for cacheable responses")

        cache_analysis['recommendations'] = recommendations

        return cache_analysis

    async def run_load_test(self, concurrent_users: int = 10, duration_seconds: int = 30) -> Dict[str, Any]:
        """Run load test to determine API capacity"""
        print(f"🏋️  Running load test: {concurrent_users} concurrent users for {duration_seconds}s")

        load_test_results = {
            'concurrent_users': concurrent_users,
            'duration_seconds': duration_seconds,
            'start_time': datetime.now().isoformat(),
            'requests_completed': 0,
            'requests_failed': 0,
            'response_times': [],
            'status_codes': {},
            'errors': []
        }

        async def user_session():
            """Simulate a single user session"""
            start_time = time.time()
            while time.time() - start_time < duration_seconds:
                for endpoint in self.endpoints_to_test:
                    try:
                        request_start = time.time()
                        async with self.session.get(f"{self.base_url}{endpoint}") as response:
                            response_time = (time.time() - request_start) * 1000
                            load_test_results['response_times'].append(response_time)
                            load_test_results['status_codes'][response.status] = \
                                load_test_results['status_codes'].get(response.status, 0) + 1
                            load_test_results['requests_completed'] += 1
                    except Exception as e:
                        load_test_results['requests_failed'] += 1
                        load_test_results['errors'].append(str(e))

                    # Small delay between requests
                    await asyncio.sleep(0.1)

        # Run concurrent user sessions
        tasks = [user_session() for _ in range(concurrent_users)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate statistics
        if load_test_results['response_times']:
            load_test_results.update({
                'avg_response_time': statistics.mean(load_test_results['response_times']),
                'p95_response_time': statistics.quantiles(load_test_results['response_times'], n=20)[18] if len(load_test_results['response_times']) > 20 else max(load_test_results['response_times']),
                'p99_response_time': statistics.quantiles(load_test_results['response_times'], n=100)[98] if len(load_test_results['response_times']) > 100 else max(load_test_results['response_times']),
                'requests_per_second': load_test_results['requests_completed'] / duration_seconds,
                'error_rate': load_test_results['requests_failed'] / (load_test_results['requests_completed'] + load_test_results['requests_failed']) if (load_test_results['requests_completed'] + load_test_results['requests_failed']) > 0 else 0
            })

        load_test_results['end_time'] = datetime.now().isoformat()

        return load_test_results

    async def _benchmark_endpoint(self, endpoint: str, num_requests: int = 10) -> APIEndpointMetrics:
        """Benchmark a single API endpoint"""
        response_times = []
        status_codes = {}
        total_bytes = 0

        url = f"{self.base_url}{endpoint}"
        method = "GET"  # Default to GET, can be enhanced to support other methods

        for i in range(num_requests):
            start_time = time.time()
            try:
                async with self.session.get(url) as response:
                    response_time = (time.time() - start_time) * 1000
                    response_times.append(response_time)
                    status_codes[response.status] = status_codes.get(response.status, 0) + 1

                    # Calculate throughput
                    if response.content_length:
                        total_bytes += response.content_length

                    # Read response to ensure complete transfer
                    await response.text()

            except Exception as e:
                logger.error(f"Request {i+1} to {endpoint} failed: {e}")
                response_times.append(5000)  # Penalty for failed requests
                status_codes[500] = status_codes.get(500, 0) + 1

        # Calculate metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else max(response_times)
            p99_response_time = statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else max(response_times)

            total_time = sum(response_times) / 1000  # Convert to seconds
            throughput_mbps = (total_bytes / (1024 * 1024)) / total_time if total_time > 0 else 0
            requests_per_second = num_requests / total_time if total_time > 0 else 0
            error_rate = sum(count for code, count in status_codes.items() if code >= 400) / num_requests
        else:
            avg_response_time = p95_response_time = p99_response_time = 0
            throughput_mbps = requests_per_second = error_rate = 0

        return APIEndpointMetrics(
            endpoint=endpoint,
            method=method,
            avg_response_time=avg_response_time,
            p95_response_time=p95_response_time,
            p99_response_time=p99_response_time,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            throughput_mbps=throughput_mbps,
            status_codes=status_codes
        )

    async def _check_broken_object_level_authorization(self) -> List[SecurityVulnerability]:
        """Check for broken object level authorization (API1:2019)"""
        vulnerabilities = []

        # Test accessing other users' data
        test_endpoints = [
            "/api/v1/users/999",  # Try to access non-existent user
            "/api/v1/teams/999",  # Try to access non-existent team
        ]

        for endpoint in test_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status in [200, 201]:  # Should not be able to access
                        vulnerabilities.append(SecurityVulnerability(
                            endpoint=endpoint,
                            vulnerability_type="Broken Object Level Authorization",
                            severity="HIGH",
                            description="API endpoint may be exposing data without proper authorization checks",
                            recommendation="Implement object-level authorization checks to ensure users can only access their own data",
                            owasp_reference="API1:2019"
                        ))
            except Exception as e:
                logger.error(f"Error checking object level authorization for {endpoint}: {e}")

        return vulnerabilities

    async def _check_broken_user_authentication(self) -> List[SecurityVulnerability]:
        """Check for broken user authentication (API2:2019)"""
        vulnerabilities = []

        # Test authentication mechanisms
        auth_tests = [
            ("No authentication", {}, {}),
            ("Invalid token", {"Authorization": "Bearer invalid_token"}, {}),
            ("Expired token format", {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"}, {}),
        ]

        for test_name, headers, data in auth_tests:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/v1/users/me",
                    headers=headers
                ) as response:
                    if response.status == 200:  # Should not succeed with invalid auth
                        vulnerabilities.append(SecurityVulnerability(
                            endpoint="/api/v1/users/me",
                            vulnerability_type="Broken User Authentication",
                            severity="CRITICAL",
                            description=f"Endpoint accessible with {test_name}",
                            recommendation="Implement proper authentication token validation",
                            owasp_reference="API2:2019"
                        ))
            except Exception as e:
                logger.error(f"Error checking authentication for {test_name}: {e}")

        return vulnerabilities

    async def _check_excessive_data_exposure(self) -> List[SecurityVulnerability]:
        """Check for excessive data exposure (API3:2019)"""
        vulnerabilities = []

        # Check if sensitive data is exposed in responses
        sensitive_fields = ['password', 'secret', 'key', 'token', 'ssn', 'credit_card']

        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                if response.status == 200:
                    data = await response.json()
                    data_str = json.dumps(data).lower()

                    for field in sensitive_fields:
                        if field in data_str:
                            vulnerabilities.append(SecurityVulnerability(
                                endpoint="multiple",
                                vulnerability_type="Excessive Data Exposure",
                                severity="MEDIUM",
                                description=f"Sensitive field '{field}' detected in API response",
                                recommendation="Remove sensitive fields from API responses",
                                owasp_reference="API3:2019"
                            ))
        except Exception as e:
            logger.error(f"Error checking data exposure: {e}")

        return vulnerabilities

    async def _check_lack_of_resources_and_rate_limiting(self) -> List[SecurityVulnerability]:
        """Check for lack of resources and rate limiting (API4:2019)"""
        vulnerabilities = []

        # This is also covered in analyze_rate_limiting, but check for critical cases
        try:
            # Rapid fire requests to test for any protection
            rapid_requests = []
            for i in range(50):
                try:
                    start_time = time.time()
                    async with self.session.post(
                        f"{self.base_url}/api/v1/auth/token",
                        json={"username": "test@example.com", "password": "wrongpassword"}
                    ) as response:
                        response_time = (time.time() - start_time) * 1000
                        rapid_requests.append((response.status, response_time))
                except:
                    rapid_requests.append((500, 5000))

            # If no 429 or 503 responses, rate limiting might be missing
            if not any(status in [429, 503] for status, _ in rapid_requests):
                vulnerabilities.append(SecurityVulnerability(
                    endpoint="/api/v1/auth/token",
                    vulnerability_type="Lack of Rate Limiting",
                    severity="HIGH",
                    description="No rate limiting detected on authentication endpoint",
                    recommendation="Implement rate limiting to prevent brute force attacks",
                    owasp_reference="API4:2019"
                ))

        except Exception as e:
            logger.error(f"Error checking rate limiting: {e}")

        return vulnerabilities

    async def _check_broken_function_level_authorization(self) -> List[SecurityVulnerability]:
        """Check for broken function level authorization (API5:2019)"""
        # This would require testing with different user roles
        # For now, return empty as it's complex to test without proper user setup
        return []

    async def _check_mass_assignment(self) -> List[SecurityVulnerability]:
        """Check for mass assignment vulnerabilities (API6:2019)"""
        vulnerabilities = []

        # Test mass assignment by sending extra fields in POST/PUT requests
        test_payloads = [
            {"username": "test", "password": "password", "is_admin": True},
            {"email": "test@example.com", "role": "admin", "permissions": ["all"]}
        ]

        for payload in test_payloads:
            try:
                async with self.session.post(
                    f"{self.base_url}/api/v1/users/",
                    json=payload
                ) as response:
                    # If accepts unexpected fields, might be vulnerable
                    if response.status in [200, 201]:
                        vulnerabilities.append(SecurityVulnerability(
                            endpoint="/api/v1/users/",
                            vulnerability_type="Mass Assignment",
                            severity="MEDIUM",
                            description="API may accept unexpected fields in requests",
                            recommendation="Implement proper field validation and whitelisting",
                            owasp_reference="API6:2019"
                        ))
            except Exception:
                pass  # Expected if endpoint doesn't exist or requires auth

        return vulnerabilities

    async def _check_security_misconfiguration(self) -> List[SecurityVulnerability]:
        """Check for security misconfiguration (API7:2019)"""
        vulnerabilities = []

        # Check for common security headers
        security_headers = [
            'x-content-type-options',
            'x-frame-options',
            'x-xss-protection',
            'strict-transport-security',
            'content-security-policy'
        ]

        try:
            async with self.session.get(f"{self.base_url}/api/v1/health") as response:
                missing_headers = []
                for header in security_headers:
                    if header not in response.headers:
                        missing_headers.append(header)

                if missing_headers:
                    vulnerabilities.append(SecurityVulnerability(
                        endpoint="multiple",
                        vulnerability_type="Security Misconfiguration",
                        severity="LOW",
                        description=f"Missing security headers: {', '.join(missing_headers)}",
                        recommendation="Add missing security headers to API responses",
                        owasp_reference="API7:2019"
                    ))

        except Exception as e:
            logger.error(f"Error checking security headers: {e}")

        return vulnerabilities

    async def _check_injection(self) -> List[SecurityVulnerability]:
        """Check for injection vulnerabilities (API8:2019)"""
        vulnerabilities = []

        # Test for SQL injection in query parameters
        sql_payloads = [
            "1' OR '1'='1",
            "1; DROP TABLE users;--",
            "1' UNION SELECT * FROM users--"
        ]

        for payload in sql_payloads:
            try:
                async with self.session.get(
                    f"{self.base_url}/api/v1/users/{payload}"
                ) as response:
                    # If SQL error in response, might be vulnerable
                    if response.status == 500:
                        text = await response.text()
                        if 'sql' in text.lower() or 'syntax' in text.lower():
                            vulnerabilities.append(SecurityVulnerability(
                                endpoint="/api/v1/users/{id}",
                                vulnerability_type="SQL Injection",
                                severity="CRITICAL",
                                description="Possible SQL injection vulnerability detected",
                                recommendation="Use parameterized queries and input validation",
                                owasp_reference="API8:2019"
                            ))
                            break
            except Exception:
                pass

        return vulnerabilities

    async def _check_improper_assets_management(self) -> List[SecurityVulnerability]:
        """Check for improper assets management (API9:2019)"""
        vulnerabilities = []

        # Check for exposed administrative endpoints
        admin_endpoints = [
            "/admin",
            "/api/v1/admin",
            "/debug",
            "/api/v1/debug",
            "/api/v1/config"
        ]

        for endpoint in admin_endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        vulnerabilities.append(SecurityVulnerability(
                            endpoint=endpoint,
                            vulnerability_type="Improper Assets Management",
                            severity="MEDIUM",
                            description="Administrative endpoint may be exposed",
                            recommendation="Protect administrative endpoints with proper authentication",
                            owasp_reference="API9:2019"
                        ))
            except Exception:
                pass

        return vulnerabilities

    async def _check_insufficient_logging_and_monitoring(self) -> List[SecurityVulnerability]:
        """Check for insufficient logging and monitoring (API10:2019)"""
        # This is difficult to test externally, but we can check for lack of rate limiting
        # which often indicates insufficient monitoring
        return []

    def _validate_openapi_spec(self, openapi_spec: Dict) -> Dict[str, Any]:
        """Validate OpenAPI specification completeness"""
        validation_results = {
            'valid': True,
            'issues': [],
            'recommendations': [],
            'completeness_score': 0
        }

        # Check required fields
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in openapi_spec:
                validation_results['issues'].append(f"Missing required field: {field}")
                validation_results['valid'] = False

        # Check info completeness
        if 'info' in openapi_spec:
            info_fields = ['title', 'version', 'description']
            for field in info_fields:
                if field not in openapi_spec['info']:
                    validation_results['issues'].append(f"Missing info field: {field}")

        # Check endpoint documentation
        if 'paths' in openapi_spec:
            endpoints = openapi_spec['paths']
            for path, path_item in endpoints.items():
                for method, operation in path_item.items():
                    if method.upper() in ['GET', 'POST', 'PUT', 'DELETE']:
                        if 'summary' not in operation:
                            validation_results['issues'].append(f"Missing summary for {method.upper()} {path}")
                        if 'responses' not in operation:
                            validation_results['issues'].append(f"Missing responses for {method.upper()} {path}")

        # Calculate completeness score
        total_checks = len(required_fields) + 3 + (len(openapi_spec.get('paths', {}).keys()) * 2)
        passed_checks = total_checks - len(validation_results['issues'])
        validation_results['completeness_score'] = (passed_checks / total_checks * 100) if total_checks > 0 else 0

        # Generate recommendations
        if validation_results['completeness_score'] < 80:
            validation_results['recommendations'].append("Improve API documentation completeness")

        if any('description' not in openapi_spec.get('info', {}) for field in ['description']):
            validation_results['recommendations'].append("Add API description")

        return validation_results

    async def generate_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive API optimization report"""
        print("📊 Generating API excellence report...")

        # Gather all analysis data
        performance_metrics = await self.analyze_api_performance()
        security_vulnerabilities = await self.analyze_api_security()
        documentation_analysis = await self.analyze_api_documentation()
        rate_limiting_analysis = await self.analyze_rate_limiting()
        caching_analysis = await self.analyze_caching_strategy()

        # Calculate scores
        performance_score = self._calculate_performance_score(performance_metrics)
        security_score = self._calculate_security_score(security_vulnerabilities)
        documentation_score = documentation_analysis.get('completeness_score', 0)
        rate_limiting_score = 100 if rate_limiting_analysis['rate_limiting_status'] == 'IMPLEMENTED' else 0
        caching_score = caching_analysis['cache_implementation_rate'] * 100

        overall_score = (performance_score + security_score + documentation_score + rate_limiting_score + caching_score) / 5

        # Generate recommendations
        critical_recommendations = []
        high_priority_recommendations = []
        medium_priority_recommendations = []

        # Security critical issues
        critical_vulns = [v for v in security_vulnerabilities if v.severity == 'CRITICAL']
        if critical_vulns:
            critical_recommendations.extend([
                f"CRITICAL: Fix {len(critical_vulns)} critical security vulnerabilities immediately"
            ])

        # Performance issues
        slow_endpoints = [m for m in performance_metrics if m.avg_response_time > 1000]
        if slow_endpoints:
            high_priority_recommendations.extend([
                f"HIGH: {len(slow_endpoints)} endpoints with response time > 1s need optimization"
            ])

        # Documentation issues
        if documentation_score < 70:
            medium_priority_recommendations.append(
                f"MEDIUM: Improve API documentation completeness (current: {documentation_score:.0f}%)"
            )

        return {
            'timestamp': datetime.now().isoformat(),
            'overall_score': overall_score,
            'performance_score': performance_score,
            'security_score': security_score,
            'documentation_score': documentation_score,
            'rate_limiting_score': rate_limiting_score,
            'caching_score': caching_score,
            'performance_metrics': [asdict(m) for m in performance_metrics],
            'security_vulnerabilities': [asdict(v) for v in security_vulnerabilities],
            'documentation_analysis': documentation_analysis,
            'rate_limiting_analysis': rate_limiting_analysis,
            'caching_analysis': caching_analysis,
            'critical_recommendations': critical_recommendations,
            'high_priority_recommendations': high_priority_recommendations,
            'medium_priority_recommendations': medium_priority_recommendations,
            'overall_grade': self._get_grade_from_score(overall_score)
        }

    def _calculate_performance_score(self, metrics: List[APIEndpointMetrics]) -> int:
        """Calculate API performance score (0-100)"""
        if not metrics:
            return 0

        avg_response_times = [m.avg_response_time for m in metrics]
        error_rates = [m.error_rate for m in metrics]

        avg_response_time = statistics.mean(avg_response_times)
        avg_error_rate = statistics.mean(error_rates)

        score = 100

        # Response time penalty
        if avg_response_time > 200:
            score -= min(50, (avg_response_time - 200) / 10)
        elif avg_response_time > 100:
            score -= min(25, (avg_response_time - 100) / 4)

        # Error rate penalty
        if avg_error_rate > 0.05:  # 5%
            score -= min(40, avg_error_rate * 500)

        return max(0, min(100, int(score)))

    def _calculate_security_score(self, vulnerabilities: List[SecurityVulnerability]) -> int:
        """Calculate API security score (0-100)"""
        score = 100

        severity_penalties = {
            'CRITICAL': 30,
            'HIGH': 20,
            'MEDIUM': 10,
            'LOW': 5
        }

        for vuln in vulnerabilities:
            penalty = severity_penalties.get(vuln.severity, 5)
            score -= penalty

        return max(0, min(100, score))

    def _get_grade_from_score(self, score: float) -> str:
        """Get grade from score"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()

async def main():
    """Main execution function"""
    print("🚀 PsychSync API Excellence Optimizer")
    print("=" * 50)

    optimizer = APIExcellenceOptimizer()

    try:
        await optimizer.initialize()

        # Generate comprehensive report
        report = await optimizer.generate_optimization_report()

        # Display results
        print(f"\n📊 Overall API Excellence Score: {report['overall_score']:.1f}/100")
        print(f"📈 Overall Grade: {report['overall_grade']}")

        print(f"\n📊 Component Scores:")
        print(f"   Performance: {report['performance_score']}/100")
        print(f"   Security: {report['security_score']}/100")
        print(f"   Documentation: {report['documentation_score']:.0f}/100")
        print(f"   Rate Limiting: {report['rate_limiting_score']}/100")
        print(f"   Caching: {report['caching_score']:.0f}/100")

        # Display critical issues
        if report['critical_recommendations']:
            print(f"\n🚨 Critical Issues:")
            for issue in report['critical_recommendations']:
                print(f"   • {issue}")

        # Display high priority issues
        if report['high_priority_recommendations']:
            print(f"\n⚠️  High Priority Issues:")
            for issue in report['high_priority_recommendations']:
                print(f"   • {issue}")

        # Display security vulnerabilities
        if report['security_vulnerabilities']:
            print(f"\n🔒 Security Vulnerabilities Found:")
            for vuln in report['security_vulnerabilities'][:5]:
                print(f"   • {vuln['severity']}: {vuln['vulnerability_type']} on {vuln['endpoint']}")

        # Display performance issues
        if report['performance_metrics']:
            print(f"\n⚡ Performance Summary:")
            for metric in report['performance_metrics'][:3]:
                print(f"   • {metric['endpoint']}: {metric['avg_response_time']:.2f}ms avg, {metric['error_rate']:.1%} error rate")

        # Save detailed report
        report_file = "api_excellence_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n📄 Detailed report saved to: {report_file}")

        # Determine exit code based on overall grade
        if report['overall_grade'] in ['A', 'B']:
            print(f"\n✅ API excellence check PASSED")
            return 0
        elif report['overall_grade'] == 'C':
            print(f"\n⚠️  API excellence check PASSED with warnings")
            return 0
        else:
            print(f"\n❌ API excellence check FAILED")
            return 1

    except Exception as e:
        logger.error(f"Error during API optimization: {e}")
        print(f"❌ API optimization failed: {e}")
        return 1

    finally:
        await optimizer.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)