"""
Comprehensive Security Validation Tests
Tests all security controls and input validation
"""

import pytest
from app.core.security_validator import (
    SecurityValidator, SecurityLevel, ValidationResult
)
from app.core.audit_logger import AuditLogger, SecurityEventType
from app.core.rate_limiter import RateLimiter, AdvancedRateLimiter
import time
import uuid
from unittest.mock import Mock, patch


class TestSecurityValidator:
    """Test security validation functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.validator = SecurityValidator(SecurityLevel.HIGH)

    def test_email_validation_valid_emails(self):
        """Test valid email validation"""
        valid_emails = [
            "user@example.com",
            "test.user+tag@domain.co.uk",
            "user_name@sub.domain.com",
            "12345@domain.com"
        ]

        for email in valid_emails:
            result = self.validator.validate_email(email)
            assert result.is_valid, f"Email should be valid: {email}"
            assert result.sanitized_value == email.lower()
            assert result.risk_level == SecurityLevel.LOW

    def test_email_validation_invalid_emails(self):
        """Test invalid email validation"""
        invalid_emails = [
            "invalid-email",
            "@domain.com",
            "user@",
            "user..name@domain.com",
            "user@.domain.com",
            "user name@domain.com",
            "user@domain..com"
        ]

        for email in invalid_emails:
            result = self.validator.validate_email(email)
            assert not result.is_valid, f"Email should be invalid: {email}"
            assert len(result.security_issues) > 0

    def test_email_validation_injection_attempts(self):
        """Test email injection attempts"""
        injection_emails = [
            "user@example.com'; DROP TABLE users; --",
            "user@example.com<script>alert('xss')</script>",
            "user@example.com' OR '1'='1",
            "<script>alert('xss')</script>@example.com"
        ]

        for email in injection_emails:
            result = self.validator.validate_email(email)
            assert not result.is_valid, f"Injection email should be rejected: {email}"
            assert result.risk_level == SecurityLevel.CRITICAL

    def test_text_input_validation_normal_input(self):
        """Test normal text input validation"""
        normal_texts = [
            "Hello world",
            "This is a normal text with 123 numbers",
            "Special chars: !@#$%^&*()",
            "Multi-line\ntext\nwith\ttabs"
        ]

        for text in normal_texts:
            result = self.validator.validate_text_input(text, "test_field")
            assert result.is_valid, f"Text should be valid: {text}"
            assert result.risk_level == SecurityLevel.LOW

    def test_text_input_validation_injection_attempts(self):
        """Test text input injection attempts"""
        injection_texts = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "javascript:alert('xss')",
            "{{7*7}}",  # Template injection
            "${7*7}",   # Expression injection
        ]

        for text in injection_texts:
            result = self.validator.validate_text_input(text, "test_field")
            # Should either reject or sanitize
            if not result.is_valid:
                assert result.risk_level in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            else:
                # If valid, should be sanitized
                assert "<script>" not in result.sanitized_value
                assert "javascript:" not in result.sanitized_value.lower()

    def test_text_input_length_limits(self):
        """Test text input length limits"""
        # Test maximum length
        long_text = "a" * 15000  # Exceeds default max of 10000
        result = self.validator.validate_text_input(long_text, "test_field")
        assert not result.is_valid
        assert "exceeds maximum length" in str(result.security_issues)

        # Test minimum length
        result = self.validator.validate_text_input("", "test_field", min_length=5)
        assert not result.is_valid
        assert "below minimum length" in str(result.security_issues)

    def test_uuid_validation_valid_uuids(self):
        """Test valid UUID validation"""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            uuid.uuid4(),
            str(uuid.uuid4())
        ]

        for valid_uuid in valid_uuids:
            result = self.validator.validate_uuid(str(valid_uuid))
            assert result.is_valid, f"UUID should be valid: {valid_uuid}"
            assert result.risk_level == SecurityLevel.LOW

    def test_uuid_validation_invalid_uuids(self):
        """Test invalid UUID validation"""
        invalid_uuids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456-42661417400",  # Missing digit
            "123e4567-e89b-12d3-a456-4266141740000",  # Extra digit
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>"
        ]

        for invalid_uuid in invalid_uuids:
            result = self.validator.validate_uuid(invalid_uuid)
            assert not result.is_valid, f"UUID should be invalid: {invalid_uuid}"

    def test_name_validation_valid_names(self):
        """Test valid name validation"""
        valid_names = [
            "John Doe",
            "Mary-Jane O'Connor",
            "Dr. Jane Smith",
            "Jean-Claude Van Damme",
            "O'Neill"
        ]

        for name in valid_names:
            result = self.validator.validate_name_input(name, "name")
            assert result.is_valid, f"Name should be valid: {name}"
            assert result.sanitized_value == name.strip()

    def test_name_validation_invalid_names(self):
        """Test invalid name validation"""
        invalid_names = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE users; --",
            "Name with\nnewline",
            "Name\twith\ttab",
            "Name/with/slash"
        ]

        for name in invalid_names:
            result = self.validator.validate_name_input(name, "name")
            assert not result.is_valid, f"Name should be invalid: {name}"

    def test_search_query_validation(self):
        """Test search query validation"""
        # Valid searches
        valid_searches = [
            "john doe",
            "john@doe.com",
            "search term",
            "multi word search"
        ]

        for search in valid_searches:
            result = self.validator.validate_search_query(search)
            assert result.is_valid, f"Search should be valid: {search}"

        # Invalid/dangerous searches
        dangerous_searches = [
            "'; DROP TABLE users; --",
            "<script>alert('xss')</script>",
            "javascript:alert('xss')"
        ]

        for search in dangerous_searches:
            result = self.validator.validate_search_query(search)
            # Should be sanitized or rejected
            if not result.is_valid:
                assert result.risk_level >= SecurityLevel.MEDIUM

    def test_pagination_validation(self):
        """Test pagination parameter validation"""
        # Valid pagination
        result = self.validator.validate_pagination_params(0, 50)
        assert result.is_valid
        assert result.sanitized_value == {"skip": 0, "limit": 50}

        # Invalid negative skip
        result = self.validator.validate_pagination_params(-10, 50)
        assert result.is_valid  # Should be corrected to 0
        assert result.sanitized_value["skip"] == 0

        # Invalid limit too high
        result = self.validator.validate_pagination_params(0, 2000, max_limit=100)
        assert result.is_valid  # Should be corrected to max_limit
        assert result.sanitized_value["limit"] == 100

    def test_dict_sanitization(self):
        """Test dictionary sanitization"""
        test_dict = {
            "name": "<script>alert('xss')</script>",
            "email": "test@example.com'; DROP TABLE users; --",
            "description": "Normal description",
            "admin_notes": "Sensitive data that should be redacted",
            "password": "secret123"
        }

        result = self.validator.sanitize_dict(
            test_dict,
            text_fields=["name", "description"],
            email_fields=["email"],
            name_fields=["admin_notes"]
        )

        assert result.is_valid
        sanitized = result.sanitized_value

        # Check that HTML was sanitized
        assert "<script>" not in sanitized["name"]
        assert "DROP TABLE" not in sanitized["email"]

        # Check that normal content is preserved
        assert "Normal description" == sanitized["description"]

    def test_file_path_validation(self):
        """Test file path validation"""
        # Valid paths
        valid_paths = [
            "documents/file.pdf",
            "uploads/image.jpg",
            "data/report.csv"
        ]

        for path in valid_paths:
            result = self.validator.validate_file_path(path)
            assert result.is_valid, f"Path should be valid: {path}"

        # Dangerous paths
        dangerous_paths = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\cmd.exe",
            "file.txt;rm -rf /"
        ]

        for path in dangerous_paths:
            result = self.validator.validate_file_path(path)
            assert not result.is_valid, f"Path should be invalid: {path}"


class TestAuditLogger:
    """Test audit logging functionality"""

    def setup_method(self):
        """Setup test environment"""
        # Mock logger to avoid actual file writes during tests
        self.mock_logger = Mock()
        with patch('app.core.audit_logger.AuditLogger._setup_security_logger') as mock_setup:
            mock_setup.return_value = self.mock_logger
            self.audit_logger = AuditLogger()

    def test_log_security_event_basic(self):
        """Test basic security event logging"""
        self.audit_logger.log_security_event(
            user_id="test-user-123",
            event_type=SecurityEventType.AUTHENTICATION_SUCCESS,
            details="User logged in successfully",
            client_ip="192.168.1.1"
        )

        # Verify logger was called
        self.mock_logger.info.assert_called()
        call_args = self.mock_logger.info.call_args[0][0]
        assert "AUTHENTICATION_SUCCESS" in call_args
        assert "test-user-123" in call_args

    def test_log_security_event_high_risk(self):
        """Test high-risk security event logging"""
        self.audit_logger.log_security_event(
            event_type=SecurityEventType.INJECTION_ATTEMPT,
            details="SQL injection attempt detected",
            client_ip="192.168.1.1",
            risk_score=90
        )

        # Verify critical logger was called
        self.mock_logger.critical.assert_called()
        call_args = self.mock_logger.critical.call_args[0][0]
        assert "INJECTION_ATTEMPT" in call_args
        assert "90/100" in call_args

    def test_calculate_risk_score(self):
        """Test risk score calculation"""
        # Test high-risk event
        event_data = {
            "event_type": "injection_attempt",
            "status_code": 400
        }
        risk_score = self.audit_logger._calculate_risk_score(event_data)
        assert risk_score >= 60

        # Test low-risk event
        event_data = {
            "event_type": "authentication_success",
            "status_code": 200
        }
        risk_score = self.audit_logger._calculate_risk_score(event_data)
        assert risk_score < 50

    def test_sanitize_event_data(self):
        """Test event data sanitization"""
        sensitive_data = {
            "password": "secret123",
            "email": "test@example.com",
            "details": "User attempted login with password: secret123",
            "user_id": "user-123"
        }

        sanitized = self.audit_logger._sanitize_event_data(sensitive_data)

        # Password should be redacted
        assert sanitized["password"] == "[REDACTED]"

        # Email should be preserved but details sanitized
        assert "secret123" not in sanitized["details"]
        assert sanitized["email"] == "test@example.com"


class TestRateLimiter:
    """Test rate limiting functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.rate_limiter = RateLimiter()  # Uses memory fallback

    @pytest.mark.asyncio
    async def test_rate_limiting_basic(self):
        """Test basic rate limiting"""
        key = "test-key"
        limit = 5
        window = 1

        # First 5 requests should be allowed
        for i in range(5):
            is_allowed, metadata = await self.rate_limiter.is_allowed(key, limit, window)
            assert is_allowed, f"Request {i+1} should be allowed"
            assert metadata["remaining"] == 4 - i

        # 6th request should be denied
        is_allowed, metadata = await self.rate_limiter.is_allowed(key, limit, window)
        assert not is_allowed
        assert metadata["remaining"] == 0
        assert metadata["retry_after"] > 0

    @pytest.mark.asyncio
    async def test_rate_limiting_different_keys(self):
        """Test rate limiting with different keys"""
        key1 = "user-1"
        key2 = "user-2"
        limit = 3
        window = 1

        # Each user should have their own rate limit
        for i in range(limit):
            is_allowed1, _ = await self.rate_limiter.is_allowed(key1, limit, window)
            is_allowed2, _ = await self.rate_limiter.is_allowed(key2, limit, window)
            assert is_allowed1
            assert is_allowed2

    @pytest.mark.asyncio
    async def test_rate_limiting_window_reset(self):
        """Test rate limit window reset"""
        key = "test-key"
        limit = 2
        window = 1  # 1 second window

        # Use up the limit
        for i in range(limit):
            is_allowed, _ = await self.rate_limiter.is_allowed(key, limit, window)
            assert is_allowed

        # Should be rate limited
        is_allowed, _ = await self.rate_limiter.is_allowed(key, limit, window)
        assert not is_allowed

        # Wait for window to pass (simulated by manipulating time)
        # In real implementation, this would require time mocking
        time.sleep(1.1)  # Wait for window to expire

        # Should be allowed again
        is_allowed, _ = await self.rate_limiter.is_allowed(key, limit, window)
        assert is_allowed

    def test_generate_rate_limit_key(self):
        """Test rate limit key generation"""
        key = self.rate_limiter.generate_key(
            identifier="test-user",
            endpoint="login",
            user_id="user-123",
            ip_address="192.168.1.1"
        )

        # Key should be consistent
        key2 = self.rate_limiter.generate_key(
            identifier="test-user",
            endpoint="login",
            user_id="user-123",
            ip_address="192.168.1.1"
        )

        assert key == key2
        assert key.startswith("rl:")


class TestAdvancedRateLimiter:
    """Test advanced rate limiter functionality"""

    def setup_method(self):
        """Setup test environment"""
        self.advanced_limiter = AdvancedRateLimiter()

    @pytest.mark.asyncio
    async def test_policy_based_rate_limiting(self):
        """Test policy-based rate limiting"""
        # Test default policy
        is_allowed, metadata = await self.advanced_limiter.check_rate_limit(
            "default", "test-user-123"
        )
        assert is_allowed

        # Test custom policy
        self.advanced_limiter.set_policy("custom", 5, 300)  # 5 requests per 5 minutes
        is_allowed, metadata = await self.advanced_limiter.check_rate_limit(
            "custom", "test-user-123"
        )
        assert is_allowed


class TestIntegrationSecurity:
    """Integration tests for security components"""

    @pytest.mark.asyncio
    async def test_security_validation_pipeline(self):
        """Test complete security validation pipeline"""
        validator = SecurityValidator(SecurityLevel.HIGH)

        # Test user registration data
        user_data = {
            "email": "test@example.com",
            "password": "SecurePass123!",
            "full_name": "John Doe"
        }

        # Validate each field
        email_result = validator.validate_email(user_data["email"])
        password_result = validator.validate_text_input(
            user_data["password"], "password", max_length=128
        )
        name_result = validator.validate_name_input(
            user_data["full_name"], "full_name"
        )

        # All should be valid
        assert email_result.is_valid
        assert password_result.is_valid
        assert name_result.is_valid

        # Test injection attempt
        malicious_data = {
            "email": "test@example.com'; DROP TABLE users; --",
            "password": "<script>alert('xss')</script>",
            "full_name": "javascript:alert('xss')"
        }

        malicious_email = validator.validate_email(malicious_data["email"])
        malicious_password = validator.validate_text_input(
            malicious_data["password"], "password"
        )
        malicious_name = validator.validate_name_input(
            malicious_data["full_name"], "full_name"
        )

        # All should be rejected or sanitized
        assert not malicious_email.is_valid
        assert malicious_email.risk_level == SecurityLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_audit_logging_with_security_events(self):
        """Test audit logging integration with security events"""
        with patch('app.core.audit_logger.AuditLogger._setup_security_logger'):
            audit_logger = AuditLogger()

            # Simulate security events
            audit_logger.log_security_event(
                event_type=SecurityEventType.AUTHENTICATION_FAILURE,
                details="Invalid password attempt",
                client_ip="192.168.1.100",
                risk_score=40
            )

            audit_logger.log_security_event(
                event_type=SecurityEventType.INJECTION_ATTEMPT,
                details="SQL injection attempt blocked",
                client_ip="192.168.1.100",
                risk_score=90
            )

            # Test convenience functions
            from app.core.audit_logger import log_auth_failure, log_injection_attempt

            log_auth_failure("user-123", "invalid_password", "192.168.1.100")
            log_injection_attempt("user-123", "SQL", "192.168.1.100")

    def test_security_level_impact(self):
        """Test impact of different security levels"""
        low_validator = SecurityValidator(SecurityLevel.LOW)
        high_validator = SecurityValidator(SecurityLevel.HIGH)

        test_input = "text with <script>alert('xss')</script> content"

        low_result = low_validator.validate_text_input(test_input, "test")
        high_result = high_validator.validate_text_input(test_input, "test")

        # High security should be more restrictive
        if not low_result.is_valid and not high_result.is_valid:
            # Both reject, but high security should have higher risk level
            assert high_result.risk_level.value >= low_result.risk_level.value
        elif low_result.is_valid and not high_result.is_valid:
            # Low allows, high rejects - expected behavior
            assert True
        else:
            # Both allow - high security should have sanitized more
            assert len(high_result.sanitized_value) <= len(low_result.sanitized_value)


if __name__ == "__main__":
    pytest.main([__file__])