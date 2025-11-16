"""
Unit Tests for Security Module

Tests authentication, authorization, password hashing, JWT tokens, etc.
"""
import pytest
from datetime import datetime, timedelta
from jose import jwt, JWTError
from unittest.mock import Mock, patch

from app.core.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    decode_access_token
)
from app.core.config import settings


class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hashing(self):
        """Test that passwords are hashed correctly"""
        password = "MySecurePassword123!"
        hashed = get_password_hash(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Hash should be bcrypt format
        assert hashed.startswith('$2b$')
        
        # Hash should be deterministic (same input = same output)
        hashed2 = get_password_hash(password)
        assert verify_password(password, hashed2)
    
    def test_password_verification_success(self):
        """Test verifying correct password"""
        password = "CorrectPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test verifying incorrect password"""
        password = "CorrectPassword123!"
        wrong_password = "WrongPassword123!"
        hashed = get_password_hash(password)
        
        assert verify_password(wrong_password, hashed) is False
    
    def test_empty_password(self):
        """Test handling of empty password"""
        with pytest.raises(ValueError):
            get_password_hash("")
    
    def test_special_characters_in_password(self):
        """Test passwords with special characters"""
        password = "P@$$w0rd!#$%^&*()"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True
    
    def test_unicode_password(self):
        """Test passwords with unicode characters"""
        password = "Pässwörd123密码"
        hashed = get_password_hash(password)
        
        assert verify_password(password, hashed) is True


class TestJWTTokens:
    """Test JWT token creation and verification"""
    
    def test_create_access_token(self):
        """Test creating JWT access token"""
        user_data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data=user_data)
        
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Token should have 3 parts (header.payload.signature)
        parts = token.split('.')
        assert len(parts) == 3
    
    def test_decode_access_token(self):
        """Test decoding valid JWT token"""
        user_data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data=user_data)
        
        decoded = decode_access_token(token)
        
        assert decoded is not None
        assert decoded.get("sub") == "user@example.com"
        assert decoded.get("user_id") == 123
    
    def test_token_expiration(self):
        """Test that tokens expire correctly"""
        user_data = {"sub": "user@example.com"}
        
        # Create token with 1 second expiration
        token = create_access_token(
            data=user_data,
            expires_delta=timedelta(seconds=1)
        )
        
        # Token should be valid immediately
        decoded = decode_access_token(token)
        assert decoded is not None
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Token should be expired
        decoded = decode_access_token(token)
        assert decoded is None
    
    def test_invalid_token_format(self):
        """Test handling of invalid token format"""
        invalid_token = "not.a.valid.token"
        
        decoded = decode_access_token(invalid_token)
        assert decoded is None
    
    def test_tampered_token(self):
        """Test that tampered tokens are rejected"""
        user_data = {"sub": "user@example.com", "user_id": 123}
        token = create_access_token(data=user_data)
        
        # Tamper with token
        parts = token.split('.')
        parts[1] = parts[1][:-5] + "AAAAA"  # Modify payload
        tampered_token = '.'.join(parts)
        
        decoded = decode_access_token(tampered_token)
        assert decoded is None
    
    def test_token_with_additional_claims(self):
        """Test tokens with custom claims"""
        user_data = {
            "sub": "user@example.com",
            "user_id": 123,
            "role": "admin",
            "organization_id": 456
        }
        token = create_access_token(data=user_data)
        
        decoded = decode_access_token(token)
        
        assert decoded.get("role") == "admin"
        assert decoded.get("organization_id") == 456


class TestAuthorization:
    """Test authorization and permission checks"""
    
    def test_admin_authorization(self):
        """Test admin role authorization"""
        from app.core.security import has_role
        
        user = Mock(role="admin")
        
        assert has_role(user, "admin") is True
        assert has_role(user, "user") is True  # Admin can do user things
    
    def test_user_authorization(self):
        """Test regular user authorization"""
        from app.core.security import has_role
        
        user = Mock(role="user")
        
        assert has_role(user, "user") is True
        assert has_role(user, "admin") is False  # User cannot do admin things
    
    def test_resource_ownership(self):
        """Test checking resource ownership"""
        from app.core.security import is_owner
        
        user = Mock(id=123)
        resource = Mock(user_id=123)
        
        assert is_owner(user, resource) is True
        
        other_resource = Mock(user_id=456)
        assert is_owner(user, other_resource) is False
    
    def test_team_membership(self):
        """Test checking team membership"""
        from app.core.security import is_team_member
        
        user = Mock(id=123)
        team = Mock(member_ids=[123, 456, 789])
        
        assert is_team_member(user, team) is True
        
        other_user = Mock(id=999)
        assert is_team_member(other_user, team) is False


class TestInputValidation:
    """Test input validation and sanitization"""
    
    def test_email_validation(self):
        """Test email format validation"""
        from app.core.security import validate_email
        
        valid_emails = [
            "user@example.com",
            "john.doe@company.co.uk",
            "test+tag@domain.com"
        ]
        
        invalid_emails = [
            "invalid",
            "@example.com",
            "user@",
            "user space@example.com",
            "user@domain",
            ""
        ]
        
        for email in valid_emails:
            assert validate_email(email) is True, f"Expected {email} to be valid"
        
        for email in invalid_emails:
            assert validate_email(email) is False, f"Expected {email} to be invalid"
    
    def test_sql_injection_prevention(self):
        """Test SQL injection prevention"""
        from app.core.security import sanitize_input
        
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "<script>alert('xss')</script>"
        ]
        
        for input_str in malicious_inputs:
            sanitized = sanitize_input(input_str)
            # Should remove or escape dangerous characters
            assert "DROP TABLE" not in sanitized
            assert "<script>" not in sanitized
    
    def test_xss_prevention(self):
        """Test XSS attack prevention"""
        from app.core.security import escape_html
        
        xss_inputs = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')"
        ]
        
        for input_str in xss_inputs:
            escaped = escape_html(input_str)
            assert "<script>" not in escaped
            assert "<img" not in escaped
            assert "javascript:" not in escaped


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    def test_rate_limit_not_exceeded(self):
        """Test that requests under limit are allowed"""
        from app.core.security import check_rate_limit
        
        user_id = 123
        
        # First few requests should succeed
        for _ in range(5):
            assert check_rate_limit(user_id, limit=10, window=60) is True
    
    def test_rate_limit_exceeded(self):
        """Test that requests over limit are blocked"""
        from app.core.security import check_rate_limit
        
        user_id = 456
        limit = 3
        
        # First 3 requests succeed
        for _ in range(limit):
            assert check_rate_limit(user_id, limit=limit, window=60) is True
        
        # Next request should fail
        assert check_rate_limit(user_id, limit=limit, window=60) is False
    
    def test_rate_limit_reset(self):
        """Test that rate limit resets after window"""
        from app.core.security import check_rate_limit, reset_rate_limit
        
        user_id = 789
        
        # Exhaust limit
        for _ in range(3):
            check_rate_limit(user_id, limit=3, window=60)
        
        # Should be blocked
        assert check_rate_limit(user_id, limit=3, window=60) is False
        
        # Reset limit
        reset_rate_limit(user_id)
        
        # Should work again
        assert check_rate_limit(user_id, limit=3, window=60) is True


class TestCSRFProtection:
    """Test CSRF token functionality"""
    
    def test_generate_csrf_token(self):
        """Test CSRF token generation"""
        from app.core.security import generate_csrf_token
        
        token = generate_csrf_token()
        
        assert isinstance(token, str)
        assert len(token) > 20
    
    def test_validate_csrf_token(self):
        """Test CSRF token validation"""
        from app.core.security import generate_csrf_token, validate_csrf_token
        
        token = generate_csrf_token()
        
        # Valid token should pass
        assert validate_csrf_token(token) is True
        
        # Invalid token should fail
        assert validate_csrf_token("invalid_token") is False
    
    def test_csrf_token_expiration(self):
        """Test that CSRF tokens expire"""
        from app.core.security import generate_csrf_token, validate_csrf_token
        
        token = generate_csrf_token(expires_in=1)  # 1 second
        
        # Should be valid immediately
        assert validate_csrf_token(token) is True
        
        # Wait for expiration
        import time
        time.sleep(2)
        
        # Should be expired
        assert validate_csrf_token(token) is False


class TestSecureHeaders:
    """Test security headers"""
    
    def test_security_headers_present(self):
        """Test that security headers are set"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.get("/")
        
        # Check for security headers
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"
        
        assert "X-XSS-Protection" in response.headers
    
    def test_cors_headers(self):
        """Test CORS headers configuration"""
        from fastapi.testclient import TestClient
        from app.main import app
        
        client = TestClient(app)
        response = client.options("/api/v1/health")
        
        # Check CORS headers
        assert "Access-Control-Allow-Origin" in response.headers


class TestPasswordPolicy:
    """Test password policy enforcement"""
    
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected"""
        from app.core.security import validate_password_strength
        
        weak_passwords = [
            "password",
            "12345678",
            "qwerty",
            "abc123"
        ]
        
        for password in weak_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is False
            assert message is not None
    
    def test_strong_password_accepted(self):
        """Test that strong passwords are accepted"""
        from app.core.security import validate_password_strength
        
        strong_passwords = [
            "MySecure123!Password",
            "C0mpl3x@P@ssw0rd",
            "Str0ng#Passw0rd!"
        ]
        
        for password in strong_passwords:
            is_valid, message = validate_password_strength(password)
            assert is_valid is True
    
    def test_password_min_length(self):
        """Test minimum password length"""
        from app.core.security import validate_password_strength
        
        short_password = "Abc1!"
        is_valid, message = validate_password_strength(short_password, min_length=8)
        assert is_valid is False
        assert "length" in message.lower()
    
    def test_password_requires_special_char(self):
        """Test that password requires special character"""
        from app.core.security import validate_password_strength
        
        no_special = "Password123"
        is_valid, message = validate_password_strength(
            no_special,
            require_special=True
        )
        assert is_valid is False
        assert "special" in message.lower()


class TestSessionManagement:
    """Test session management"""
    
    def test_create_session(self):
        """Test creating user session"""
        from app.core.security import create_session
        
        user_id = 123
        session = create_session(user_id)
        
        assert session is not None
        assert session.get("user_id") == user_id
        assert "session_id" in session
    
    def test_invalidate_session(self):
        """Test invalidating user session"""
        from app.core.security import create_session, invalidate_session
        
        user_id = 123
        session = create_session(user_id)
        session_id = session["session_id"]
        
        # Invalidate session
        result = invalidate_session(session_id)
        assert result is True
    
    def test_validate_session(self):
        """Test validating active session"""
        from app.core.security import create_session, validate_session
        
        user_id = 123
        session = create_session(user_id)
        session_id = session["session_id"]
        
        # Session should be valid
        is_valid = validate_session(session_id)
        assert is_valid is True


class TestEncryption:
    """Test encryption utilities"""
    
    def test_encrypt_decrypt_data(self):
        """Test encrypting and decrypting data"""
        from app.core.security import encrypt_data, decrypt_data
        
        sensitive_data = "This is sensitive information"
        
        encrypted = encrypt_data(sensitive_data)
        
        # Encrypted data should be different
        assert encrypted != sensitive_data
        
        # Should be able to decrypt
        decrypted = decrypt_data(encrypted)
        assert decrypted == sensitive_data
    
    def test_hash_sensitive_data(self):
        """Test one-way hashing of sensitive data"""
        from app.core.security import hash_data
        
        data = "sensitive_identifier"
        hashed = hash_data(data)
        
        # Hash should be consistent
        assert hash_data(data) == hashed
        
        # Hash should be different from original
        assert hashed != data


class TestAuditLogging:
    """Test security audit logging"""
    
    def test_log_login_attempt(self):
        """Test logging login attempts"""
        from app.core.security import log_login_attempt
        
        result = log_login_attempt(
            user_id=123,
            success=True,
            ip_address="192.168.1.1"
        )
        
        assert result is True
    
    def test_log_failed_login(self):
        """Test logging failed login attempts"""
        from app.core.security import log_login_attempt
        
        result = log_login_attempt(
            user_id=None,
            success=False,
            ip_address="192.168.1.1",
            reason="Invalid password"
        )
        
        assert result is True
    
    def test_detect_brute_force(self):
        """Test detecting brute force attacks"""
        from app.core.security import detect_brute_force
        
        ip_address = "192.168.1.100"
        
        # Simulate multiple failed attempts
        for _ in range(5):
            log_login_attempt(None, False, ip_address)
        
        # Should detect brute force
        is_brute_force = detect_brute_force(ip_address)
        assert is_brute_force is True


if __name__ == '__main__':
    pytest.main([__file__, '-v'])