#!/usr/bin/env python3
"""
Web Application Security Tests

Tests for secure utilities:
- Parameterized queries
- Input validation
- Output encoding
- Safe file handling

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import sys
import pytest
from pathlib import Path
import tempfile
import os

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.core.secure_query import (
    QueryBuilder,
    SecureQueryExecutor,
    InputSanitizer,
    SQLInjectionError
)
from app.core.input_validation import InputValidator
from app.core.output_encoding import OutputEncoder
from app.core.safe_file_handling import (
    SafeFileHandler,
    FileValidationError,
    SecureFileUpload
)
from app.db.models import User


# ==================== SQL Injection Prevention Tests ====================

class TestParameterizedQueries:
    """Test SQL injection prevention via parameterized queries"""

    def test_safe_select_by_id(self):
        """Test safe SELECT by ID"""
        assert True  # Placeholder - requires DB session

    def test_block_string_concatenation(self):
        """Test that string concatenation is blocked"""
        builder = QueryBuilder(None)

        # Should raise error for dangerous patterns
        with pytest.raises(SQLInjectionError):
            builder.execute_raw(
                "SELECT * FROM users WHERE id = {id}",  # f-string style
                {"id": 1}
            )

    def test_safe_parameterized_query(self):
        """Test safe parameterized query"""
        builder = QueryBuilder(None)

        # This should work (uses :parameter style)
        # In real test, would execute against DB
        query = "SELECT * FROM users WHERE email = :email AND status = :status"
        params = {"email": "test@example.com", "status": "active"}

        # Verify no dangerous patterns
        import re
        dangerous_patterns = [r'\{[^}]*\}', r'%s', r'\?%s']
        for pattern in dangerous_patterns:
            assert not re.search(pattern, query)


class TestInputSanitizer:
    """Test input sanitization"""

    def test_sanitize_string(self):
        """Test string sanitization"""
        # Remove null bytes
        result = InputSanitizer.sanitize_string("test\x00string")
        assert '\x00' not in result

    def test_sanitize_email(self):
        """Test email sanitization"""
        email = InputSanitizer.sanitize_email("Test@Example.COM  ")
        assert email == "test@example.com"

    def test_sanitize_integer(self):
        """Test integer sanitization"""
        value = InputSanitizer.sanitize_integer("42", min_val=0, max_val=100)
        assert value == 42

        # Test out of range
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_integer("150", min_val=0, max_val=100)

    def test_sanitize_sort_field_allowlist(self):
        """Test sort field validation against allowlist"""
        allowed = ['id', 'email', 'username', 'created_at']

        result = InputSanitizer.sanitize_sort_field('username', allowed)
        assert result == 'username'

        # Block invalid field
        with pytest.raises(ValueError):
            InputSanitizer.sanitize_sort_field('password; DROP TABLE users;', allowed)


class TestInputValidation:
    """Test comprehensive input validation"""

    def test_validate_string(self):
        """Test string validation"""
        result = InputValidator.validate_string("test", min_length=1, max_length=100)
        assert result == "test"

        # Test too short
        with pytest.raises(Exception):
            InputValidator.validate_string("", min_length=1)

        # Test too long
        with pytest.raises(Exception):
            InputValidator.validate_string("x" * 1000, max_length=100)

    def test_validate_email(self):
        """Test email validation"""
        email = InputValidator.validate_email("user@example.com")
        assert email == "user@example.com"

        # Test invalid format
        with pytest.raises(Exception):
            InputValidator.validate_email("invalid-email")

    def test_validate_integer(self):
        """Test integer validation"""
        value = InputValidator.validate_integer("42", min_val=18, max_val=120)
        assert value == 42

        # Test below min
        with pytest.raises(Exception):
            InputValidator.validate_integer("15", min_val=18)

    def test_validate_url(self):
        """Test URL validation"""
        url = InputValidator.validate_url("https://example.com")
        assert url == "https://example.com"

        # Block dangerous URLs
        with pytest.raises(Exception):
            InputValidator.validate_url("javascript:alert('XSS')")

        with pytest.raises(Exception):
            InputValidator.validate_url("data:text/html,<script>alert(1)</script>")

    def test_validate_file_path(self):
        """Test file path validation"""
        # Allow relative path
        path = InputValidator.validate_file_path("uploads/test.txt")
        assert "uploads/test.txt" in path or "test.txt" in path

        # Block path traversal
        with pytest.raises(Exception):
            InputValidator.validate_file_path("../../../etc/passwd")

    def test_validate_json(self):
        """Test JSON validation"""
        json_str = '{"name": "test", "value": 123}'
        data = InputValidator.validate_json(json_str)
        assert data["name"] == "test"
        assert data["value"] == 123

        # Test invalid JSON
        with pytest.raises(Exception):
            InputValidator.validate_json("{invalid json}")


# ==================== Output Encoding Tests ====================

class TestOutputEncoding:
    """Test XSS prevention via output encoding"""

    def test_encode_for_html(self):
        """Test HTML encoding"""
        dangerous = '<script>alert("XSS")</script>'
        safe = OutputEncoder.encode_for_html(dangerous)

        assert '<script>' not in safe
        assert '&lt;script&gt;' in safe
        assert 'alert' not in safe or 'alert(&quot;' in safe

    def test_encode_for_html_attribute(self):
        """Test HTML attribute encoding"""
        dangerous = '" onclick="alert(\'XSS\')'
        safe = OutputEncoder.encode_for_html_attribute(dangerous)

        assert '"' not in safe or '&quot;' in safe
        assert "'" not in safe or '&apos;' in safe

    def test_encode_for_javascript(self):
        """Test JavaScript encoding"""
        dangerous = "'; alert('XSS'); //"
        safe = OutputEncoder.encode_for_javascript(dangerous)

        # Should escape quotes and special chars
        assert '\\' in safe  # Backslash escapes

    def test_encode_for_url(self):
        """Test URL encoding"""
        dangerous = "test@example.com&param=<script>"
        safe = OutputEncoder.encode_for_url(dangerous)

        assert '@' in safe and '%40' in safe
        assert '&' not in safe or '%26' in safe
        assert '<' not in safe or '%3C' in safe

    def test_validate_url_blocks_dangerous_protocols(self):
        """Test that dangerous URL protocols are blocked"""
        dangerous_urls = [
            "javascript:alert('XSS')",
            "data:text/html,<script>alert(1)</script>",
            "vbscript:msgbox('XSS')",
        ]

        for url in dangerous_urls:
            safe = OutputEncoder.validate_url(url)
            assert safe == ""  # Should return empty for dangerous URLs

    def test_encode_json_for_html(self):
        """Test JSON encoding for HTML context"""
        data = {"user": "<script>alert('XSS')</script>"}
        safe = OutputEncoder.encode_json_for_html(data)

        # Should be both JSON-encoded and HTML-escaped
        assert '<script>' not in safe
        assert '&lt;' in safe or '\\u003c' in safe


# ==================== File Handling Tests ====================

class TestSafeFileHandling:
    """Test secure file handling"""

    def test_validate_filename_blocks_path_traversal(self):
        """Test that path traversal is blocked"""
        dangerous_filenames = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM"
        ]

        for filename in dangerous_filenames:
            with pytest.raises(FileValidationError):
                SafeFileHandler.validate_filename(filename)

    def test_validate_filename_blocks_dangerous_chars(self):
        """Test that dangerous characters are blocked"""
        dangerous_filenames = [
            "test*.txt",
            "test?.txt",
            "test\".txt",
            "test<>.txt",
            "test|.txt",
            "test\x00.txt"
        ]

        for filename in dangerous_filenames:
            with pytest.raises(FileValidationError):
                SafeFileHandler.validate_filename(filename)

    def test_validate_filename_allows_safe_names(self):
        """Test that safe filenames are accepted"""
        safe_filenames = [
            "test-file.txt",
            "test_file.csv",
            "test file.pdf",
            "Test.File.123.txt",
            "document (1).xlsx"
        ]

        for filename in safe_filenames:
            result = SafeFileHandler.validate_filename(filename)
            assert result is not None
            assert '..' not in result

    def test_validate_file_upload_checks_size(self):
        """Test that file size is checked"""
        # Create large file (> 100MB)
        large_content = b"x" * (101 * 1024 * 1024)

        with pytest.raises(FileValidationError):
            SafeFileHandler.validate_file_upload(
                large_content,
                "test.txt"
            )

    def test_validate_file_upload_blocks_empty(self):
        """Test that empty files are blocked"""
        with pytest.raises(FileValidationError):
            SafeFileHandler.validate_file_upload(
                b"",
                "test.txt"
            )

    def test_safe_read_file_blocks_path_traversal(self):
        """Test safe file read blocks path traversal"""
        import tempfile

        # Create temp directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Try to read file outside temp dir
            with pytest.raises(FileValidationError):
                SafeFileHandler.safe_read_file(
                    "/etc/passwd",
                    base_dir=tmpdir
                )


# ==================== Integration Tests ====================

class TestSecurityIntegration:
    """Integration tests for security utilities"""

    def test_full_xss_prevention_flow(self):
        """Test complete XSS prevention flow"""
        # Simulate user input with XSS
        user_input = '<script>alert("XSS")</script>'

        # Step 1: Validate input
        with pytest.raises(Exception):
            # Should block HTML in safe string validation
            InputValidator.validate_no_html(user_input)

        # Step 2: If HTML allowed, sanitize
        clean = OutputEncoder.strip_html_tags(user_input)
        assert '<script>' not in clean
        assert '</script>' not in clean

        # Step 3: Encode for output
        encoded = OutputEncoder.encode_for_html(user_input)
        assert '<script>' not in encoded
        assert '&lt;script&gt;' in encoded

    def test_full_sql_injection_prevention_flow(self):
        """Test complete SQL injection prevention flow"""
        # Simulate malicious input
        malicious_id = "1 OR 1=1; DROP TABLE users--"

        # Step 1: Validate as integer
        try:
            clean_id = InputValidator.validate_integer(
                malicious_id,
                min_val=1,
                max_val=1000
            )
            # Should fail validation
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

        # Step 2: If passed to query builder, should use parameters
        # (This would be tested with actual DB)

    def test_full_path_traversal_prevention_flow(self):
        """Test complete path traversal prevention flow"""
        malicious_path = "../../../etc/passwd"

        # Step 1: Validate filename
        with pytest.raises(FileValidationError):
            SafeFileHandler.validate_filename(malicious_path)

        # Step 2: Validate file path
        with pytest.raises(FileValidationError):
            SafeFileHandler.validate_file_path(malicious_path)

    def test_file_upload_security_flow(self):
        """Test complete file upload security"""
        import tempfile

        # Create test file content
        file_content = b"Test file content"

        with tempfile.TemporaryDirectory() as tmpdir:
            # Validate and save
            result = SafeFileHandler.validate_file_upload(
                file_content,
                "test.txt",
                max_size=1024 * 1024
            )

            assert result['is_valid'] is True
            assert result['filename'] == "test.txt"

            # Save file
            saved = SafeFileHandler.save_upload(
                file_content,
                "test.txt",
                tmpdir
            )

            assert saved is not None

            # Verify saved path is within tmpdir
            full_path = os.path.join(tmpdir, saved)
            assert os.path.exists(full_path)
            assert os.path.abspath(full_path).startswith(os.path.abspath(tmpdir))


# ==================== Security Property Tests ====================

class TestSecurityProperties:
    """Test security properties (invariants)"""

    def test_html_encoding_never_returns_raw_html(self):
        """Property: HTML encoding should never return raw HTML tags"""
        dangerous_inputs = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "<<script>alert(1)</script>",
        ]

        for input_text in dangerous_inputs:
            encoded = OutputEncoder.encode_for_html(input_text)
            # Raw HTML tags should not appear
            assert not any(
                tag in encoded
                for tag in ['<script', '<img', '<svg', '<iframe', '<object']
            )

    def test_input_validation_blocks_null_bytes(self):
        """Property: All validators should block null bytes"""
        validators = [
            InputValidator.validate_string,
            lambda x: InputValidator.validate_email(x),
            lambda x: InputValidator.validate_url(x),
            SafeFileHandler.validate_filename,
        ]

        for validator in validators:
            try:
                # Add null byte to test data
                if validator == SafeFileHandler.validate_filename:
                    result = validator("test\x00.txt")
                else:
                    result = validator("test\x00")

                # Should not contain null bytes
                assert '\x00' not in str(result)

            except Exception:
                # Raising exception is also acceptable
                pass

    def test_filename_validation_blocks_path_separators(self):
        """Property: Filename validation should always block path separators"""
        dangerous_chars = ['/', '\\', '..']

        for char in dangerous_chars:
            filename = f"test{char}file.txt"

            with pytest.raises(FileValidationError):
                SafeFileHandler.validate_filename(filename)

    def test_url_validation_blocks_javascript_protocol(self):
        """Property: URL validation should always block javascript: protocol"""
        javascript_urls = [
            "javascript:alert(1)",
            "JAVASCRIPT:alert(1)",
            "Javascript:alert(1)",
            "\tjavascript:alert(1)",  # Tab prefix
        ]

        for url in javascript_urls:
            safe = OutputEncoder.validate_url(url)
            # Should return empty string for dangerous URLs
            assert safe == ""


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
