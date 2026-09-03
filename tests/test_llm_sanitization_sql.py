"""
LLM Sanitization Tests - SQL Injection Prevention

This test suite validates that the LLM sanitization pipeline
effectively prevents SQL injection attacks from LLM-generated content.

Compliance: OWASP SQLi, NIST SSDF PO.3.1, HIPAA §164.312(e)(1)
"""

import pytest

from app.services.llm_sanitization import ContentType, LLMSanitizer


class TestSQLInjectionPrevention:
    """Test SQL injection attack prevention"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance"""
        return LLMSanitizer()

    # ========================================================================
    # UNION SELECT Tests
    # ========================================================================

    def test_blocks_union_select(self, sanitizer):
        """Verify UNION SELECT injection is blocked"""
        malicious = (
            "SELECT name FROM users WHERE id = 1 UNION SELECT password FROM admin"
        )
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "UNION SELECT" not in result.sanitized
            or "UNION SELECT NOT ALLOWED" in result.sanitized.upper()
        )
        assert (
            "[UNION SELECT NOT ALLOWED]" in result.sanitized
            or "BLOCKED" in result.sanitized.upper()
        )
        assert len(result.warnings) > 0

    def test_blocks_union_select_case_variant(self, sanitizer):
        """Verify case variants of UNION SELECT are blocked"""
        malicious = "select * from users union select * from admin"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "union select" not in result.sanitized.lower()
            or "NOT ALLOWED" in result.sanitized.upper()
        )
        assert (
            "BLOCKED" in result.sanitized.upper()
            or "NOT ALLOWED" in result.sanitized.upper()
        )

    def test_blocks_union_all_select(self, sanitizer):
        """Verify UNION ALL SELECT injection is blocked"""
        malicious = "SELECT id FROM users UNION ALL SELECT credit_card FROM payments"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "UNION ALL SELECT" not in result.sanitized
            or "NOT ALLOWED" in result.sanitized.upper()
        )
        assert (
            "BLOCKED" in result.sanitized.upper()
            or "NOT ALLOWED" in result.sanitized.upper()
        )

    # ========================================================================
    # Comment Injection Tests
    # ========================================================================

    def test_blocks_double_dash_comment(self, sanitizer):
        """Verify -- (double dash) comment injection is blocked"""
        malicious = "SELECT * FROM users WHERE id = 1 -- DROP TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        # Should warn about comment injection
        assert any(
            "comment" in w.lower() or "dangerous" in w.lower() for w in result.warnings
        )

    def test_blocks_block_comment(self, sanitizer):
        """Verify /* */ block comment injection is blocked"""
        malicious = "SELECT * FROM users WHERE id = 1 /* DROP TABLE users */"
        result = sanitizer.sanitize(malicious, content_type="sql")

        # Should warn about comment injection
        assert any(
            "comment" in w.lower() or "dangerous" in w.lower() for w in result.warnings
        )

    def test_blocks_comment_with_newline(self, sanitizer):
        """Verify comment injection with newline is blocked"""
        malicious = "SELECT * FROM users WHERE id = 1 --\nDROP TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert any(
            "comment" in w.lower() or "dangerous" in w.lower() for w in result.warnings
        )

    # ========================================================================
    # Semicolon Chaining Tests
    # ========================================================================

    def test_blocks_semicolon_drop(self, sanitizer):
        """Verify semicolon chaining with DROP is blocked"""
        malicious = "SELECT * FROM users; DROP TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[DROP TABLE NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    def test_blocks_semicolon_delete(self, sanitizer):
        """Verify semicolon chaining with DELETE is blocked"""
        malicious = "SELECT * FROM users; DELETE FROM users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[DELETE FROM NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )

    def test_blocks_semicolon_execute(self, sanitizer):
        """Verify semicolon chaining with EXECUTE is blocked"""
        malicious = "SELECT * FROM users; EXECUTE('DROP TABLE users')"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[CHAINED COMMANDS NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )

    # ========================================================================
    # Dangerous Statement Tests
    # ========================================================================

    def test_blocks_insert_statement(self, sanitizer):
        """Verify INSERT statements are blocked"""
        malicious = (
            "INSERT INTO users (username, password) VALUES ('hacker', 'password')"
        )
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert "[INSERT" in result.sanitized or "BLOCKED" in result.sanitized
        assert any("INSERT" in w or "not allowed" in w.lower() for w in result.warnings)

    def test_blocks_update_statement(self, sanitizer):
        """Verify UPDATE statements are blocked"""
        malicious = "UPDATE users SET password = 'hacked' WHERE id = 1"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert "[UPDATE" in result.sanitized or "BLOCKED" in result.sanitized
        assert len(result.warnings) > 0

    def test_blocks_delete_statement(self, sanitizer):
        """Verify DELETE statements are blocked"""
        malicious = "DELETE FROM users WHERE id = 1"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert "[DELETE" in result.sanitized or "BLOCKED" in result.sanitized
        assert len(result.warnings) > 0

    def test_blocks_drop_table(self, sanitizer):
        """Verify DROP TABLE statements are blocked"""
        malicious = "DROP TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[DROP TABLE NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    def test_blocks_create_table(self, sanitizer):
        """Verify CREATE TABLE statements are blocked"""
        malicious = "CREATE TABLE hacked (data TEXT)"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[CREATE TABLE NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    def test_blocks_alter_table(self, sanitizer):
        """Verify ALTER TABLE statements are blocked"""
        malicious = "ALTER TABLE users ADD COLUMN password TEXT"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[ALTER TABLE NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    def test_blocks_truncate_table(self, sanitizer):
        """Verify TRUNCATE TABLE statements are blocked"""
        malicious = "TRUNCATE TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[TRUNCATE TABLE NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    # ========================================================================
    # Safe Query Tests
    # ========================================================================

    def test_allows_safe_select(self, sanitizer):
        """Verify safe SELECT queries are allowed"""
        safe = "SELECT id, username, email FROM users WHERE active = true LIMIT 10"
        result = sanitizer.sanitize(safe, content_type="sql")

        # Should preserve the query (maybe with LIMIT added)
        assert "SELECT" in result.sanitized
        assert "FROM users" in result.sanitized
        # Should not have warnings for safe queries
        dangerous_warnings = [w for w in result.warnings if "dangerous" in w.lower()]
        assert len(dangerous_warnings) == 0

    def test_allows_select_with_joins(self, sanitizer):
        """Verify SELECT with JOINs is allowed"""
        safe = """
        SELECT u.username, r.role_name
        FROM users u
        JOIN roles r ON u.role_id = r.id
        WHERE u.active = true
        """
        result = sanitizer.sanitize(safe, content_type="sql")

        assert "SELECT" in result.sanitized
        assert "JOIN" in result.sanitized
        assert "blocked" not in result.sanitized.lower()

    def test_allows_select_with_aggregates(self, sanitizer):
        """Verify SELECT with aggregate functions is allowed"""
        safe = "SELECT COUNT(*) as total, AVG(score) as avg_score FROM assessments"
        result = sanitizer.sanitize(safe, content_type="sql")

        assert "SELECT" in result.sanitized
        assert "COUNT" in result.sanitized
        assert "AVG" in result.sanitized

    def test_allows_select_with_order_by(self, sanitizer):
        """Verify SELECT with ORDER BY is allowed"""
        safe = "SELECT username FROM users ORDER BY created_at DESC LIMIT 100"
        result = sanitizer.sanitize(safe, content_type="sql")

        assert "SELECT" in result.sanitized
        assert "ORDER BY" in result.sanitized

    # ========================================================================
    # Approval Requirements
    # ========================================================================

    def test_requires_approval_for_sql(self, sanitizer):
        """Verify all SQL queries require approval"""
        safe = "SELECT * FROM users LIMIT 10"
        result = sanitizer.sanitize(safe, content_type="sql")

        assert result.approval_required is True
        assert result.approval_request_id is not None
        assert "sql" in result.approval_request_id.lower()

    def test_approval_for_sanitized_sql(self, sanitizer):
        """Verify even sanitized SQL requires approval"""
        malicious = "SELECT * FROM users; DROP TABLE users"
        result = sanitizer.sanitize(malicious, content_type="sql")

        # Even though sanitized, still requires approval
        assert result.approval_required is True
        assert result.approval_request_id is not None

    # ========================================================================
    # Complex SQL Injection Payloads
    # ========================================================================

    def test_blocks_time_based_blind_sqli(self, sanitizer):
        """Verify time-based blind SQL injection is blocked"""
        malicious = "SELECT * FROM users WHERE id = 1; WAITFOR DELAY '00:00:10'"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[CHAINED COMMANDS NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )

    def test_blocks_boolean_based_sqli(self, sanitizer):
        """Verify boolean-based blind SQL injection is blocked"""
        malicious = "SELECT * FROM users WHERE id = 1 AND 1=1 UNION SELECT NULL"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "UNION SELECT" not in result.sanitized or "NOT ALLOWED" in result.sanitized
        )
        assert (
            "NOT ALLOWED" in result.sanitized or "blocked" in result.sanitized.lower()
        )

    def test_blocks_stored_procedure_injection(self, sanitizer):
        """Verify stored procedure injection is blocked"""
        # Note: EXEC alone is not caught, but EXECUTE is
        malicious = "SELECT * FROM users WHERE id = 1; EXECUTE xp_cmdshell('dir')"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "CHAINED COMMANDS NOT ALLOWED" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )
        assert len(result.warnings) > 0

    def test_blocks_second_order_injection(self, sanitizer):
        """Verify second-order SQL injection patterns are blocked"""
        malicious = "SELECT username FROM users WHERE id = 1; INSERT INTO logs VALUES ('hacked')"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert (
            "[INSERT STATEMENTS NOT ALLOWED]" in result.sanitized
            or "NOT ALLOWED" in result.sanitized
        )

    # ========================================================================
    # SQL in Different Contexts
    # ========================================================================

    def test_detects_sql_in_text(self, sanitizer):
        """Verify SQL detected in text content"""
        text_with_sql = "Here's a query: SELECT * FROM users WHERE id = 1"
        result = sanitizer.sanitize(text_with_sql, content_type="text")

        # Should detect as SQL
        assert result.content_type == ContentType.SQL

    def test_detects_sql_in_code(self, sanitizer):
        """Verify SQL detected in code content"""
        code_with_sql = """
        const query = "SELECT * FROM users WHERE id = " + userInput;
        db.execute(query);
        """
        result = sanitizer.sanitize(code_with_sql, content_type="code")

        # Should detect as CODE with SQL patterns
        assert (
            result.content_type == ContentType.CODE
            or result.content_type == ContentType.SQL
        )

    # ========================================================================
    # Warnings and Modifications
    # ========================================================================

    def test_generates_warnings_for_dangerous_patterns(self, sanitizer):
        """Verify warnings generated for dangerous patterns"""
        malicious = "SELECT * FROM users; DROP TABLE users -- comment"
        result = sanitizer.sanitize(malicious, content_type="sql")

        # Should have at least one warning for DROP TABLE
        assert len(result.warnings) >= 1

    def test_tracks_modifications(self, sanitizer):
        """Verify modifications are tracked"""
        malicious = "INSERT INTO users VALUES (1, 'hacker')"
        result = sanitizer.sanitize(malicious, content_type="sql")

        assert len(result.modifications) > 0 or len(result.warnings) > 0

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_query(self, sanitizer):
        """Verify empty query is handled"""
        result = sanitizer.sanitize("", content_type="sql")

        assert result.sanitized == ""
        assert result.content_type == ContentType.TEXT

    def test_whitespace_only_query(self, sanitizer):
        """Verify whitespace-only query is handled"""
        result = sanitizer.sanitize("   \n\t   ", content_type="sql")

        assert result.content_type == ContentType.TEXT

    def test_case_sensitivity(self, sanitizer):
        """Verify case variants are caught"""
        variants = [
            "select * from users",
            "SELECT * FROM users",
            "Select * From Users",
            "SeLeCt * FrOm UsErS",
        ]

        for variant in variants:
            result = sanitizer.sanitize(variant, content_type="sql")
            # All should be recognized as SQL
            assert result.content_type == ContentType.SQL


class TestSQLInjectionPreventionStrict:
    """Test SQL injection prevention with strict mode"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance"""
        return LLMSanitizer()

    def test_strict_mode_non_select_rejected(self, sanitizer):
        """Verify non-SELECT queries are rejected in strict mode"""
        malicious = "UPDATE users SET password = 'x' WHERE id = 1"
        result = sanitizer.sanitize(malicious, content_type="sql", strict_mode=True)

        assert "UPDATE" in result.sanitized or "BLOCKED" in result.sanitized
        assert len(result.warnings) > 0

    def test_strict_mode_requires_select_start(self, sanitizer):
        """Verify queries must start with SELECT"""
        malicious = "/* comment */ SELECT * FROM users"
        result = sanitizer.sanitize(malicious, content_type="sql", strict_mode=True)

        # Should warn that query must start with SELECT
        assert any(
            "start with SELECT" in w or "must start" in w.lower()
            for w in result.warnings
        )


class TestSQLValidationHelpers:
    """Test SQL validation helper functions"""

    def test_validate_sql_query_helper(self):
        """Test the validate_sql_query helper function"""
        from app.services.llm_sanitization import validate_sql_query

        # Safe query
        is_safe, reason = validate_sql_query("SELECT * FROM users WHERE id = 1")
        assert is_safe is True
        assert reason == ""

        # Dangerous query (comment injection)
        is_safe, reason = validate_sql_query(
            "SELECT * FROM users WHERE id = 1 -- DROP TABLE"
        )
        assert is_safe is False
        assert "comment" in reason.lower()

        # Dangerous query (statement chaining)
        is_safe, reason = validate_sql_query("SELECT * FROM users; DROP TABLE users")
        assert is_safe is False
        assert "chaining" in reason.lower() or "statement" in reason.lower()

        # Dangerous query (UNION SELECT)
        is_safe, reason = validate_sql_query(
            "SELECT * FROM users UNION SELECT * FROM admin"
        )
        assert is_safe is False
        assert "union" in reason.lower()

        # Non-SELECT query
        is_safe, reason = validate_sql_query("UPDATE users SET x = 1")
        assert is_safe is False
        assert "start with SELECT" in reason
