"""
LLM Output Sanitization Pipeline

This module sanitizes LLM outputs to prevent XSS, SSRF, SQL injection,
and code execution attacks. All LLM output is treated as untrusted.

Usage:
    from app.services.llm_sanitization import LLMSanitizer

    sanitizer = LLMSanitizer()
    result = sanitizer.sanitize(llm_output, content_type="text")
"""

from datetime import datetime
from enum import Enum
import html
import json
import re

from bs4 import BeautifulSoup
from pydantic import BaseModel

# ============================================================================
# Content Types
# ============================================================================

class ContentType(Enum):
    """LLM output content types"""
    TEXT = "text"
    HTML = "html"
    JSON = "json"
    CODE = "code"
    SQL = "sql"
    JAVASCRIPT = "javascript"
    UNKNOWN = "unknown"


# ============================================================================
# Dangerous Patterns
# ============================================================================

DANGEROUS_PATTERNS = {
    "html_with_script": [
        r"<script[^>]*>.*?</script>",
        r"on\w+\s*=",  # Event handlers like onclick=
        r"javascript:",
    ],
    "sql_injection": [
        r"(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|TRUNCATE)\s+",
        r";\s*(DROP|DELETE|EXECUTE)",
        r"UNION\s+SELECT",
        r"--\s*.*$",  # SQL comments
        r"/\*.*?\*/",  # SQL block comments
    ],
    "shell_command": [
        r"`[^`]+`",  # Backtick commands
        r"\$[^$]*\([^)]*\)",  # Command substitution
        r";\s*\w+",  # Command chaining
        r"\|",  # Pipe to another command
    ],
    "ssrf_url": [
        r"https?://169\.254\.169\.254",  # AWS metadata
        r"https?://127\.0\.0\.1",  # Localhost
        r"https?://0\.0\.0\.0",  # Localhost
        r"https?://192\.168\.",  # Internal network
        r"https?://10\.",  # Internal network
        r"file://",  # Local file protocol
        r"ftp://",  # FTP protocol
    ],
    "code_execution": [
        r"exec\s*\(",  # Python exec()
        r"eval\s*\(",  # Python eval()
        r"os\.system\s*\(",  # Python os.system()
        r"subprocess\.",  # Python subprocess module
        r"__import__\s*\(",  # Python dynamic import
    ],
}


# ============================================================================
# URL Allow-List
# ============================================================================

ALLOWED_URL_PATTERNS = [
    r"https://docs\.psychsync\.com/.*",
    r"https://.*\.psychsync\.com/.*",
    r"https://psychsync\.com/.*",
]


# ============================================================================
# JSON Schemas
# ============================================================================

SAFE_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "recommendations": {
            "type": "array",
            "items": {"type": "string"},
            "maxItems": 10
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1}
    },
    "required": ["summary"],
    "additionalProperties": False  # Strict mode - no extra fields
}


# ============================================================================
# Sanitization Result
# ============================================================================

class SanitizationResult(BaseModel):
    """Result of sanitizing LLM output"""

    original: str
    sanitized: str
    content_type: ContentType
    modifications: list[str]
    approval_required: bool
    approval_request_id: str | None = None
    warnings: list[str] = []


# ============================================================================
# Main Sanitizer Class
# ============================================================================

class LLMSanitizer:
    """
    LLM output sanitization pipeline

    Treats all LLM output as untrusted and applies strict sanitization.
    """

    def __init__(self):
        self.modifications = []
        self.warnings = []

    def sanitize(
        self,
        llm_output: str,
        content_type: str = "text",
        strict_mode: bool = True
    ) -> SanitizationResult:
        """
        Sanitize LLM output

        Args:
            llm_output: Raw LLM output (untrusted)
            content_type: Expected content type
            strict_mode: If True, reject unexpected content types

        Returns:
            SanitizationResult
        """

        self.modifications = []
        self.warnings = []

        # Step 1: Classify content
        detected_type = self._classify_content(llm_output)

        if strict_mode and detected_type != ContentType(content_type):
            self.warnings.append(f"Content type mismatch: expected {content_type}, detected {detected_type.value}")

        # Step 2: Apply sanitization based on detected type
        sanitized = llm_output

        if detected_type == ContentType.HTML:
            sanitized = self._sanitize_html(sanitized)

        elif detected_type == ContentType.JAVASCRIPT:
            sanitized = self._sanitize_javascript(sanitized)

        elif detected_type == ContentType.SQL:
            sanitized = self._sanitize_sql(sanitized)

        elif detected_type == ContentType.CODE:
            sanitized = self._sanitize_code(sanitized)

        # Step 3: Sanitize URLs (always)
        sanitized = self._sanitize_urls(sanitized)

        # Step 4: Sanitize images (always)
        sanitized = self._sanitize_images(sanitized)

        # Step 5: Validate JSON if applicable
        if detected_type == ContentType.JSON:
            is_valid, error = self._validate_json_schema(sanitized)
            if not is_valid:
                self.warnings.append(f"JSON validation failed: {error}")

        # Step 6: Check if approval required
        approval_required = self._requires_approval(detected_type, sanitized)

        approval_request_id = None
        if approval_required:
            approval_request_id = self._create_approval_request(
                detected_type, sanitized, self.modifications
            )

        return SanitizationResult(
            original=llm_output,
            sanitized=sanitized,
            content_type=detected_type,
            modifications=self.modifications,
            approval_required=approval_required,
            approval_request_id=approval_request_id,
            warnings=self.warnings
        )

    def _classify_content(self, content: str) -> ContentType:
        """Classify content type"""

        # Check for SQL
        if self._contains_sql(content):
            return ContentType.SQL

        # Check for JavaScript
        if self._contains_javascript(content):
            return ContentType.JAVASCRIPT

        # Check for HTML
        if self._contains_html(content):
            return ContentType.HTML

        # Check for JSON
        if self._is_json(content):
            return ContentType.JSON

        # Check for code (Python, shell, etc.)
        if self._contains_code(content):
            return ContentType.CODE

        return ContentType.TEXT

    def _sanitize_html(self, content: str) -> str:
        """Sanitize HTML by removing tags and encoding entities"""

        # Remove all HTML tags
        soup = BeautifulSoup(content, "html.parser")
        text = soup.get_text()

        # Encode HTML entities
        encoded = html.escape(text)

        self.modifications.append("Removed HTML tags and encoded entities")

        return encoded

    def _sanitize_javascript(self, content: str) -> str:
        """Remove JavaScript code"""

        original = content

        # Remove script blocks
        content = re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

        # Remove inline event handlers
        content = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', "", content)

        # Remove javascript: protocol
        content = re.sub(
            r"javascript:",
            "[REMOVED]:",
            content,
            flags=re.IGNORECASE
        )

        if content != original:
            self.modifications.append("Removed JavaScript code")
            content = "[JavaScript code removed by security policy]\n\n" + content

        return content

    def _sanitize_sql(self, content: str) -> str:
        """Sanitize SQL queries"""

        # Check for dangerous patterns
        dangerous = [
            (r"INSERT\s+INTO", "INSERT statements not allowed"),
            (r"UPDATE\s+\w+\s+SET", "UPDATE statements not allowed"),
            (r"DELETE\s+FROM", "DELETE statements not allowed"),
            (r"DROP\s+TABLE", "DROP TABLE not allowed"),
            (r"CREATE\s+TABLE", "CREATE TABLE not allowed"),
            (r"ALTER\s+TABLE", "ALTER TABLE not allowed"),
            (r"TRUNCATE\s+TABLE", "TRUNCATE TABLE not allowed"),
            (r";\s*(DROP|DELETE|EXECUTE|WAITFOR)", "Chained commands not allowed"),
            (r"UNION\s+(ALL\s+)?SELECT", "UNION SELECT not allowed"),
        ]

        for pattern, message in dangerous:
            if re.search(pattern, content, re.IGNORECASE):
                self.warnings.append(f"SQL contains dangerous pattern: {message}")
                # Use message instead of pattern to avoid regex escape issues
                content = re.sub(
                    pattern,
                    f"[{message.upper()}]",
                    content,
                    flags=re.IGNORECASE
                )

        # Only SELECT queries are safe
        if not content.strip().upper().startswith("SELECT"):
            self.warnings.append("SQL query must start with SELECT")

        return content

    def _sanitize_code(self, content: str) -> str:
        """Sanitize code snippets"""

        # Remove dangerous functions
        dangerous_funcs = [
            (r"exec\s*\(", "[EXEC] BLOCKED - dangerous function"),
            (r"eval\s*\(", "[EVAL] BLOCKED - dangerous function"),
            (r"os\.system\s*\(", "[SYSTEM] BLOCKED - dangerous function"),
        ]

        for pattern, message in dangerous_funcs:
            if re.search(pattern, content):
                content = re.sub(pattern, message, content)
                self.modifications.append(f"Removed dangerous code: {message}")

        return content

    def _sanitize_urls(self, content: str) -> str:
        """Sanitize URLs (remove or validate)"""

        # Step 1: Remove dangerous protocols (file://, ftp://, gopher://, dict://)
        dangerous_protocols = [
            (r'file://[^\s<>"{}|\\^`\[\]]*', "[FILE URL REMOVED: dangerous protocol]"),
            (r'ftp://[^\s<>"{}|\\^`\[\]]*', "[FTP URL REMOVED: dangerous protocol]"),
            (r'gopher://[^\s<>"{}|\\^`\[\]]*', "[GOPHER URL REMOVED: dangerous protocol]"),
            (r'dict://[^\s<>"{}|\\^`\[\]]*', "[DICT URL REMOVED: dangerous protocol]"),
        ]

        for pattern, replacement in dangerous_protocols:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                content = content.replace(match, replacement)
                self.modifications.append(f"Removed dangerous URL: {match[:50]}...")

        # Step 2: Find and validate HTTP/HTTPS URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)

        for url in urls:
            # Check for localhost hostname (not just IP)
            if "localhost" in url.lower() or "127.0.0.1" in url or "0.0.0.0" in url:
                content = content.replace(url, "[URL REMOVED: internal address]")
                self.modifications.append(f"Removed internal URL: {url}")
                continue

            # Check against allow-list
            allowed = any(re.match(pattern, url) for pattern in ALLOWED_URL_PATTERNS)

            if not allowed:
                # URL not in allow-list
                content = content.replace(url, "[URL REMOVED: unapproved domain]")
                self.modifications.append(f"Removed URL: {url}")

        return content

    def _sanitize_images(self, content: str) -> str:
        """Remove or validate base64 images"""

        # Remove base64 images
        content = re.sub(
            r"data:image/[^;]+;base64,[A-Za-z0-9+/=]+",
            "[IMAGE REMOVED]",
            content
        )

        return content

    def _validate_json_schema(self, content: str) -> tuple[bool, str]:
        """Validate JSON against schema"""

        try:
            data = json.loads(content)

            # Simple validation against schema
            # In production, use jsonschema library
            if "summary" not in data:
                return False, "Missing required field: summary"

            # Check for unexpected fields (strict mode)
            expected_fields = {"summary", "recommendations", "confidence"}
            for key in data:
                if key not in expected_fields:
                    return False, f"Unexpected field: {key}"

            return True, ""

        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {e!s}"

    def _requires_approval(self, content_type: ContentType, content: str) -> bool:
        """Check if content requires human approval"""

        # Always require approval for:
        # - SQL queries
        # - Code snippets (all types including JavaScript)
        # - Complex JSON with potentially dangerous fields

        if content_type == ContentType.SQL:
            return True

        if content_type == ContentType.CODE:
            return True

        if content_type == ContentType.JAVASCRIPT:
            return True

        if content_type == ContentType.JSON:
            # Check if JSON contains potentially dangerous content
            try:
                data = json.loads(content)
                if "code" in data or "sql" in data or "script" in data:
                    return True
            except:
                pass

        return False

    def _create_approval_request(
        self,
        content_type: ContentType,
        content: str,
        modifications: list[str]
    ) -> str:
        """Create approval request for content"""

        request_id = f"approve_{content_type.value}_{datetime.utcnow().timestamp()}"

        # In production, store in database
        return request_id

    # ========================================================================
    # Detection Methods
    # ========================================================================

    def _contains_sql(self, content: str) -> bool:
        """Check if content contains SQL"""
        sql_patterns = [
            r"SELECT\s+.+\s+FROM",
            r"INSERT\s+INTO",
            r"UPDATE\s+\w+\s+SET",
            r"DELETE\s+FROM",
            r"CREATE\s+TABLE",
            r"DROP\s+TABLE",
            r"ALTER\s+TABLE",
            r"TRUNCATE\s+TABLE",
            r"UNION\s+SELECT",
        ]

        return any(re.search(pattern, content, re.IGNORECASE) for pattern in sql_patterns)

    def _contains_javascript(self, content: str) -> bool:
        """Check if content contains JavaScript"""
        js_patterns = [
            r"<script[^>]*>",
            r"function\s+\w+\s*\(",
            r"const\s+\w+\s*=",
            r"let\s+\w+\s*=",
            r"var\s+\w+\s*=",
        ]

        return any(re.search(pattern, content) for pattern in js_patterns)

    def _contains_html(self, content: str) -> bool:
        """Check if content contains HTML"""
        return bool(re.search(r"<[a-z][^>]*>", content, re.IGNORECASE))

    def _is_json(self, content: str) -> bool:
        """Check if content is valid JSON"""
        try:
            json.loads(content)
            return True
        except:
            return False

    def _contains_code(self, content: str) -> bool:
        """Check if content contains code"""
        code_patterns = [
            r"def\s+\w+\s*\(",  # Python function
            r"class\s+\w+",  # Python class
            r"import\s+\w+",  # Python import
            r"from\s+\w+\s+import",  # Python from import
            r"#!/bin/bash",  # Shell script
            r"#!/usr/bin/env",  # Script shebang
        ]

        return any(re.search(pattern, content) for pattern in code_patterns)


# ============================================================================
# Helper Functions
# ============================================================================

def validate_sql_query(query: str) -> tuple[bool, str]:
    """
    Validate SQL query for safety

    Returns:
        (is_safe, reason)
    """

    # Must be SELECT only
    if not query.strip().upper().startswith("SELECT"):
        return False, "Query must start with SELECT"

    # Check for dangerous patterns
    dangerous = [
        (r"--", "SQL comment injection"),
        (r"/\*", "SQL block comment"),
        (r";", "SQL statement chaining"),
        (r"UNION\s+SELECT", "SQL injection via UNION"),
    ]

    for pattern, message in dangerous:
        if re.search(pattern, query, re.IGNORECASE):
            return False, f"Dangerous pattern detected: {message}"

    return True, ""


def validate_json_schema(data: str, schema: dict) -> tuple[bool, str]:
    """
    Validate JSON against schema

    Returns:
        (is_valid, error_message)
    """

    try:
        parsed = json.loads(data)

        # Check required fields
        for field in schema.get("required", []):
            if field not in parsed:
                return False, f"Missing required field: {field}"

        # Check for unexpected fields
        if not schema.get("additionalProperties", True):
            allowed_fields = set(schema.get("properties", {}).keys())
            for field in parsed.keys():
                if field not in allowed_fields:
                    return False, f"Unexpected field: {field}"

        return True, ""

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e!s}"


def check_for_xss(content: str) -> list[str]:
    """
    Check content for XSS payloads

    Returns:
        List of detected XSS patterns
    """

    xss_patterns = [
        "<script[^>]*>.*?</script>",
        "onload=",
        "onerror=",
        "onclick=",
        "onmouseover=",
        "javascript:",
        "<iframe",
        "<object",
        "<embed",
        "vbscript:",
        "expression(",
    ]

    detected = []

    content_lower = content.lower()

    for pattern in xss_patterns:
        if re.search(pattern, content_lower, re.IGNORECASE):
            detected.append(pattern)

    return detected


def check_for_ssrf(content: str) -> list[str]:
    """
    Check content for SSRF payloads

    Returns:
        List of detected SSRF patterns
    """

    ssrf_patterns = [
        "https://169.254.169.254",  # AWS metadata
        "http://169.254.169.254",   # AWS metadata (http)
        "https://127.0.0.1",
        "http://127.0.0.1",
        "https://0.0.0.0",
        "http://0.0.0.0",
        "https://192.168.",
        "http://192.168.",
        "https://10.",
        "http://10.",
        "file://",
        "ftp://",
        "gopher://",
        "dict://",
        "localhost",  # Localhost hostname
    ]

    detected = []

    content_lower = content.lower()
    for pattern in ssrf_patterns:
        if pattern.lower() in content_lower:
            detected.append(pattern)

    return detected
