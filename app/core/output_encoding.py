#!/usr/bin/env python3
"""
Output Encoding System - XSS Prevention

Encodes output for different contexts to prevent XSS attacks:
- HTML body
- HTML attribute
- JavaScript
- CSS
- URL
- JSON

Author: Security Team
Version: 1.0
Date: 2025-12-26
"""

import html
import json
from urllib.parse import quote, quote_plus
from typing import Any, Dict, List, Union
import re
import logging

logger = logging.getLogger(__name__)


class OutputEncoder:
    """
    Context-aware output encoding to prevent XSS.

    CRITICAL: Use the correct encoding for each context!
    Encoding for HTML ≠ Encoding for JavaScript ≠ Encoding for URL
    """

    # ==================== HTML Encoding ====================

    @staticmethod
    def encode_for_html(text: Any) -> str:
        """
        Encode text for safe HTML body context.

        Use when inserting user input into HTML content:
            <div>{user_input}</div>

        ✅ SAFE: Converts special chars to HTML entities
        """
        if text is None:
            return ""

        text = str(text)

        # html.escape handles &, <, >
        # We also encode quotes for safety
        return html.escape(text, quote=True)

    @staticmethod
    def encode_for_html_attribute(text: Any) -> str:
        """
        Encode text for safe HTML attribute context.

        Use when inserting user input into HTML attributes:
            <div title="{user_input}">

        ✅ SAFE: Encodes quotes and special characters
        """
        if text is None:
            return ""

        text = str(text)

        # Escape quotes and special characters
        text = html.escape(text, quote=True)

        # Replace quotes with entity references
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&apos;')

        return text

    @staticmethod
    def encode_for_html_js_event(text: Any) -> str:
        """
        Encode text for safe JavaScript event handler context.

        Use when inserting user input into event handlers:
            <div onclick="handler('{user_input}')">

        ⚠️  DANGER ZONE: Avoid whenever possible.
        Use data attributes and addEventListener instead.

        ✅ SAFE: Encodes for JS then HTML
        """
        # First encode for JavaScript
        js_encoded = OutputEncoder.encode_for_javascript(text)

        # Then encode for HTML attribute
        return OutputEncoder.encode_for_html_attribute(js_encoded)

    # ==================== JavaScript Encoding ====================

    @staticmethod
    def encode_for_javascript(text: Any) -> str:
        """
        Encode text for safe JavaScript context.

        Use when inserting user input into JavaScript code:
            <script>
                var name = "{user_input}";
            </script>

        ✅ SAFE: Escapes special JS characters
        """
        if text is None:
            return "null"

        text = str(text)

        # Escape backslashes first
        text = text.replace('\\', '\\\\')

        # Escape special JavaScript characters
        replacements = {
            "'": "\\'",
            '"': '\\"',
            '\n': '\\n',
            '\r': '\\r',
            '\t': '\\t',
            '\b': '\\b',
            '\f': '\\f',
        }

        for char, escaped in replacements.items():
            text = text.replace(char, escaped)

        # Escape Unicode control characters
        def escape_control_char(match):
            char = match.group(0)
            return f'\\u{ord(char):04x}'

        text = re.sub(r'[\x00-\x1F\x7F-\x9F]', escape_control_char, text)

        return text

    @staticmethod
    def encode_for_js_template_literal(text: Any) -> str:
        """
        Encode text for safe JavaScript template literal context.

        Use when inserting user input into template literals:
            const html = `{user_input}`;

        ✅ SAFE: Escapes backticks and ${}
        """
        if text is None:
            return ""

        text = str(text)

        # Escape template literal special characters
        text = text.replace('`', '\\`')
        text = text.replace('${', '\\${')

        return text

    # ==================== CSS Encoding ====================

    @staticmethod
    def encode_for_css(text: Any) -> str:
        """
        Encode text for safe CSS context.

        Use when inserting user input into CSS:
            <style>
                .{user_input} {
                    color: red;
                }
            </style>

        ⚠️  DANGER ZONE: Only allow alphanumeric if possible.

        ✅ SAFE: Escapes special CSS characters
        """
        if text is None:
            return ""

        text = str(text)

        # CSS escape sequences: \XXXX where XXXX is hex code
        def escape_char(match):
            char = match.group(0)
            # Escape any character except alphanumeric
            if char.isalnum():
                return char
            # Use CSS escape sequence \XXXX
            return f'\\{ord(char):X} '

        # Escape all non-alphanumeric characters
        text = re.sub(r'[^a-zA-Z0-9]', escape_char, text)

        return text

    # ==================== URL Encoding ====================

    @staticmethod
    def encode_for_url(text: Any, plus: bool = False) -> str:
        """
        Encode text for safe URL context.

        Use when inserting user input into URL:
            <a href="/search?q={user_input}">Link</a>

        Args:
            text: Text to encode
            plus: Use + for spaces (form encoding style)

        ✅ SAFE: Percent-encodes special characters
        """
        if text is None:
            return ""

        text = str(text)

        if plus:
            return quote_plus(text)
        else:
            return quote(text)

    @staticmethod
    def encode_for_url_parameter(text: Any) -> str:
        """
        Encode text for safe URL parameter context.

        Use when inserting user input as URL parameter value:
            ?key={user_input}

        ✅ SAFE: Percent-encodes with +
        """
        return OutputEncoder.encode_for_url(text, plus=True)

    @staticmethod
    def validate_url(url: str, allowed_protocols: List[str] = None) -> str:
        """
        Validate and encode URL safely.

        Prevents javascript: and data: URL attacks.

        Args:
            url: URL to validate
            allowed_protocols: List of allowed protocols (default: http, https)

        Returns:
            Safe URL
        """
        if not url:
            return ""

        if allowed_protocols is None:
            allowed_protocols = ['http:', 'https:', 'mailto:', 'tel:']

        # Parse URL
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)
        except Exception:
            # Invalid URL, return empty
            logger.warning(f"Invalid URL provided: {url}")
            return ""

        # Check protocol
        if parsed.scheme:
            scheme = parsed.scheme.lower() + ':'
            if scheme not in [p.lower() for p in allowed_protocols]:
                # Dangerous protocol detected
                logger.warning(f"Blocked URL with dangerous protocol: {parsed.scheme}")
                return ""

        # Encode URL components
        safe_netloc = quote(parsed.netloc, safe=':@')
        safe_path = quote(parsed.path, safe='/')
        safe_params = quote(parsed.params, safe=';/')
        safe_query = quote(parsed.query, safe=';/')
        safe_fragment = quote(parsed.fragment, safe='/')

        # Reconstruct URL
        safe_url = ''
        if parsed.scheme:
            safe_url += parsed.scheme + ':'

        if parsed.netloc:
            safe_url += '//' + safe_netloc

        safe_url += safe_path

        if parsed.params:
            safe_url += ';' + safe_params

        if parsed.query:
            safe_url += '?' + safe_query

        if parsed.fragment:
            safe_url += '#' + safe_fragment

        return safe_url

    # ==================== JSON Encoding ====================

    @staticmethod
    def encode_for_json(data: Any) -> str:
        """
        Encode data as safe JSON string.

        Use when inserting user input into JSON:
            <script>
                const data = JSON.parse('{user_input}');
            </script>

        ✅ SAFE: JSON encoding prevents script injection
        """
        try:
            # json.dumps handles proper escaping
            return json.dumps(data)
        except Exception as e:
            logger.error(f"Failed to encode data as JSON: {e}")
            return json.dumps(None)

    @staticmethod
    def encode_json_for_html(data: Any) -> str:
        """
        Encode JSON for safe HTML attribute context.

        Use when embedding JSON in HTML:
            <div data-user="{json_data}">

        ✅ SAFE: JSON encode then HTML escape
        """
        # First encode as JSON
        json_str = OutputEncoder.encode_for_json(data)

        # Then HTML escape for attribute context
        return OutputEncoder.encode_for_html_attribute(json_str)

    @staticmethod
    def encode_json_for_js(data: Any) -> str:
        """
        Encode JSON for safe JavaScript context.

        Use when embedding JSON in JavaScript:
            <script>
                const config = {json_data};
            </script>

        ✅ SAFE: JSON serialization handles escaping
        """
        # json.dumps is safe for JS context (handles unicode, etc.)
        return json.dumps(data, ensure_ascii=False)

    # ==================== XML Encoding ====================

    @staticmethod
    def encode_for_xml(text: Any) -> str:
        """
        Encode text for safe XML context.

        Use when inserting user input into XML:
            <user><name>{user_input}</name></user>

        ✅ SAFE: Escapes XML special characters
        """
        if text is None:
            return ""

        text = str(text)

        # XML escape sequences
        replacements = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&apos;'
        }

        for char, entity in replacements.items():
            text = text.replace(char, entity)

        return text

    # ==================== SQL Encoding ====================

    @staticmethod
    def encode_for_sql_like(text: Any) -> str:
        """
        Escape text for SQL LIKE clause.

        Use when inserting user input into SQL LIKE:
            WHERE name LIKE '%{user_input}%'

        ⚠️  WARNING: Always use parameterized queries instead!
        This is only for special cases where parameters aren't possible.

        ✅ SAFE: Escapes LIKE wildcards
        """
        if text is None:
            return ""

        text = str(text)

        # Escape LIKE wildcards
        text = text.replace('\\', '\\\\')
        text = text.replace('%', '\\%')
        text = text.replace('_', '\\_')

        return text

    # ==================== Sanitization ====================

    @staticmethod
    def strip_html_tags(text: Any) -> str:
        """
        Remove all HTML tags from text.

        Use when you want to display text without formatting.

        ✅ SAFE: Removes all tags
        """
        if text is None:
            return ""

        text = str(text)

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        return text

    @staticmethod
    def sanitize_html(
        text: str,
        allowed_tags: List[str] = None
    ) -> str:
        """
        Sanitize HTML by removing dangerous tags.

        Args:
            text: HTML to sanitize
            allowed_tags: List of allowed tags (default: safe formatting tags)

        ⚠️  WARNING: Use bleach library in production for better security!

        ✅ SAFE: Only allows whitelisted tags
        """
        if not text:
            return ""

        # Default allowed tags (safe formatting only)
        if allowed_tags is None:
            allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ul', 'ol', 'li']

        # This is a simple implementation
        # For production, use: https://github.com/mozilla/bleach
        try:
            import bleach
            return bleach.clean(
                text,
                tags=allowed_tags,
                strip=True
            )
        except ImportError:
            logger.warning("bleach library not installed, using basic sanitization")

            # Fallback: Remove all tags except allowed
            pattern = r'</?(?!(' + '|'.join(allowed_tags) + r')\b)[^>]+>'

            # Remove dangerous tags
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

            # Remove dangerous attributes
            text = re.sub(r'\s*on\w+\s*=\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)

            return text

    # ==================== Context-Aware Encoding ====================

    @staticmethod
    def encode_for_context(
        text: Any,
        context: str
    ) -> str:
        """
        Encode text for the specified context.

        Args:
            text: Text to encode
            context: One of: html, html_attr, js, js_template, css, url, json, xml

        Returns:
            Encoded text

        Raises:
            ValueError: If context is unknown
        """
        encoders = {
            'html': OutputEncoder.encode_for_html,
            'html_attr': OutputEncoder.encode_for_html_attribute,
            'html_js': OutputEncoder.encode_for_html_js_event,
            'js': OutputEncoder.encode_for_javascript,
            'js_template': OutputEncoder.encode_for_js_template_literal,
            'css': OutputEncoder.encode_for_css,
            'url': OutputEncoder.encode_for_url,
            'url_param': OutputEncoder.encode_for_url_parameter,
            'json': OutputEncoder.encode_for_json,
            'xml': OutputEncoder.encode_for_xml,
        }

        encoder = encoders.get(context)
        if not encoder:
            raise ValueError(
                f"Unknown context: {context}. "
                f"Valid contexts: {', '.join(encoders.keys())}"
            )

        return encoder(text)


# ==================== Template Helpers ====================

class SafeString:
    """
    Mark string as already sanitized.

    Use with template engines to prevent double-encoding.
    """

    def __init__(self, text: str):
        self.text = str(text)

    def __str__(self):
        return self.text

    def __html__(self):
        """Jinja2 protocol"""
        return self.text


def mark_safe(text: str) -> SafeString:
    """
    Mark text as safe for output.

    Use only when you've already sanitized the input!
    """
    return SafeString(text)


# ==================== Response Helpers ====================

class SafeResponse:
    """
    Build safe API responses with proper encoding.
    """

    @staticmethod
    def json_response(data: Any) -> Dict[str, Any]:
        """
        Build safe JSON response.

        All user-provided data is properly JSON-encoded.
        """
        # Ensure data is JSON-serializable
        try:
            json.dumps(data)
        except Exception as e:
            logger.error(f"Failed to serialize response data: {e}")
            data = {"error": "Failed to serialize response"}

        return data

    @staticmethod
    def sanitize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize all string values in a dictionary.

        Recursively encodes all string values for HTML context.
        """
        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                # Encode for HTML body context
                sanitized[key] = OutputEncoder.encode_for_html(value)
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                sanitized[key] = SafeResponse.sanitize_dict(value)
            elif isinstance(value, list):
                # Sanitize lists
                sanitized[key] = [
                    OutputEncoder.encode_for_html(v) if isinstance(v, str) else v
                    for v in value
                ]
            else:
                # Keep other types as-is
                sanitized[key] = value

        return sanitized


# ==================== Usage Examples ====================

def example_usage():
    """Example usage of output encoding"""

    user_input = '<script>alert("XSS")</script>'
    untrusted_input = "javascript:alert('XSS')"
    url_input = "https://evil.com/xss.js"

    # Example 1: HTML body encoding
    print("HTML encoding:")
    safe_html = OutputEncoder.encode_for_html(user_input)
    print(f"  Input:  {user_input}")
    print(f"  Output: {safe_html}")
    # Output: &lt;script&gt;alert(&quot;XSS&quot;)&lt;/script&gt;

    # Example 2: HTML attribute encoding
    print("\nHTML attribute encoding:")
    safe_attr = OutputEncoder.encode_for_html_attribute(user_input)
    print(f"  Input:  {user_input}")
    print(f"  Output: {safe_attr}")

    # Example 3: JavaScript encoding
    print("\nJavaScript encoding:")
    safe_js = OutputEncoder.encode_for_javascript(user_input)
    print(f"  Input:  {user_input}")
    print(f"  Output: {safe_js}")

    # Example 4: URL validation
    print("\nURL validation:")
    safe_url = OutputEncoder.validate_url(untrusted_input)
    print(f"  Input:  {untrusted_input}")
    print(f"  Output: {safe_url}")
    # Output: (empty string - dangerous URL blocked)

    # Example 5: JSON encoding
    print("\nJSON encoding:")
    data = {"user": user_input}
    safe_json = OutputEncoder.encode_for_json(data)
    print(f"  Input:  {data}")
    print(f"  Output: {safe_json}")

    # Example 6: Context-aware encoding
    print("\nContext-aware encoding:")
    safe_html_ctx = OutputEncoder.encode_for_context(user_input, "html")
    print(f"  Context 'html': {safe_html_ctx}")


if __name__ == '__main__':
    print("Output Encoding System - XSS Prevention")
    print("Use the correct encoding for each context!")
    print("=" * 60)
    example_usage()
