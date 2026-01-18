"""
Comprehensive Validation and Encoding Library

This module provides enterprise-grade input validation and output encoding
to prevent XSS, SQL injection, SSRF, and other injection attacks.

Compliance: OWASP ASVS v4.0, NIST SSDF, HIPAA §164.312(e)(1)

Usage:
    from app.core.validation import validate_input, encode_output

    # Validate input
    is_valid, sanitized = validate_input(
        user_input,
        "username",
        allow_list=USERNAME_ALLOWLIST
    )

    # Encode output for HTML
    safe_html = encode_output(user_input, "html")
"""

import re
import html
import json
import urllib.parse
from typing import Any, Union, List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
from ipaddress import ip_address, ip_network
import hashlib
import magic
import imghdr


# ============================================================================
# Validation Result
# ============================================================================

class ValidationSeverity(Enum):
    """Severity levels for validation failures"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ValidationResult:
    """Result of input validation"""
    is_valid: bool
    sanitized_value: Optional[Any]
    errors: List[str]
    warnings: List[str]
    severity: ValidationSeverity

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "is_valid": self.is_valid,
            "sanitized_value": self.sanitized_value,
            "errors": self.errors,
            "warnings": self.warnings,
            "severity": self.severity.value
        }


# ============================================================================
# Allow-List Definitions
# ============================================================================

class AllowLists:
    """Pre-defined allow-lists for common inputs"""

    # Username: alphanumeric, underscore, hyphen, 3-50 chars
    USERNAME = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

    # Email: basic email validation
    EMAIL = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Phone: E.164 format (optional +, digits, hyphens, spaces)
    PHONE = re.compile(r'^\+?[\d\s-]{10,20}$')

    # URL: HTTP/HTTPS only
    URL = re.compile(
        r'^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/[^\s]*)?$'
    )

    # UUID: Standard UUID format
    UUID = re.compile(
        r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
        re.IGNORECASE
    )

    # Date: ISO 8601 format
    DATE_ISO8601 = re.compile(
        r'^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?)?$'
    )

    # Assessment types
    ASSESSMENT_TYPES = {
        'big_five', 'mbti', 'enneagram', 'predictive_index',
        'strengths_finder', 'social_styles', 'custom'
    }

    # User roles
    USER_ROLES = {
        'patient', 'clinician', 'researcher', 'admin', 'super_admin'
    }

    # Allowed HTML tags (for rich text)
    HTML_TAGS_ALLOWED = {
        'p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'code'
    }

    # Allowed HTML attributes
    HTML_ATTRS_ALLOWED = {
        'href', 'title', 'alt', 'class', 'id'
    }


# ============================================================================
# Output Encoding Sinks
# ============================================================================

class OutputSink(Enum):
    """Different output contexts requiring specific encoding"""
    HTML = "html"  # HTML body
    HTML_ATTR = "html_attr"  # HTML attribute
    JS = "js"  # JavaScript
    JS_STRING = "js_string"  # JavaScript string literal
    CSS = "css"  # CSS
    URL = "url"  # URL parameter
    SQL = "sql"  # SQL query (use parameterized instead!)


# ============================================================================
# Input Validation Functions
# ============================================================================

def validate_input(
    value: Any,
    field_name: str,
    allow_list: Optional[re.Pattern] = None,
    allow_list_set: Optional[Set[str]] = None,
    max_length: Optional[int] = None,
    min_length: Optional[int] = None,
    required: bool = True,
    sanitize: bool = True
) -> ValidationResult:
    """
    Validate input against allow-list and constraints

    Args:
        value: Input value to validate
        field_name: Name of the field being validated (for error messages)
        allow_list: Regex pattern for allow-list validation
        allow_list_set: Set of allowed values for enum-like fields
        max_length: Maximum allowed length
        min_length: Minimum allowed length
        required: Whether the field is required
        sanitize: Whether to attempt sanitization of invalid input

    Returns:
        ValidationResult with validation status and sanitized value
    """

    errors = []
    warnings = []
    severity = ValidationSeverity.INFO
    sanitized = value

    # Check if required
    if required and (value is None or value == ""):
        errors.append(f"{field_name} is required")
        return ValidationResult(
            is_valid=False,
            sanitized_value=None,
            errors=errors,
            warnings=warnings,
            severity=ValidationSeverity.ERROR
        )

    # Skip further validation if not required and empty
    if not required and (value is None or value == ""):
        return ValidationResult(
            is_valid=True,
            sanitized_value="",
            errors=[],
            warnings=[],
            severity=ValidationSeverity.INFO
        )

    # Convert to string for validation
    if not isinstance(value, str):
        warnings.append(f"{field_name} converted to string")
        value = str(value)
        sanitized = value

    # Check min/max length
    if min_length and len(value) < min_length:
        errors.append(f"{field_name} must be at least {min_length} characters")
        severity = ValidationSeverity.ERROR

    if max_length and len(value) > max_length:
        errors.append(f"{field_name} must not exceed {max_length} characters")
        if sanitize:
            sanitized = value[:max_length]
            warnings.append(f"{field_name} truncated to {max_length} characters")
        severity = ValidationSeverity.ERROR

    # Validate against regex allow-list
    if allow_list and not allow_list.match(value):
        errors.append(f"{field_name} contains invalid characters")
        severity = ValidationSeverity.ERROR

        # Attempt sanitization
        if sanitize:
            # Remove characters not in allow-list
            sanitized = re.sub(allow_list.pattern.replace('^', '').replace('$', ''), '', value)
            warnings.append(f"{field_name} sanitized to remove invalid characters")

    # Validate against set allow-list
    if allow_list_set and value not in allow_list_set:
        errors.append(f"{field_name} must be one of: {', '.join(sorted(allow_list_set))}")
        severity = ValidationSeverity.ERROR

    # Check for null bytes
    if '\x00' in value:
        errors.append(f"{field_name} contains null bytes")
        if sanitize:
            sanitized = sanitized.replace('\x00', '')
            warnings.append(f"{field_name} sanitized to remove null bytes")
        severity = ValidationSeverity.CRITICAL

    # Determine overall validity
    is_valid = len(errors) == 0

    return ValidationResult(
        is_valid=is_valid,
        sanitized_value=sanitized if (sanitize or is_valid) else None,
        errors=errors,
        warnings=warnings,
        severity=severity
    )


def validate_email(email: str, required: bool = True) -> ValidationResult:
    """Validate email address"""
    return validate_input(
        email,
        "email",
        allow_list=AllowLists.EMAIL,
        max_length=255,
        required=required
    )


def validate_username(username: str, required: bool = True) -> ValidationResult:
    """Validate username"""
    return validate_input(
        username,
        "username",
        allow_list=AllowLists.USERNAME,
        required=required
    )


def validate_uuid(uuid_str: str, required: bool = True) -> ValidationResult:
    """Validate UUID format"""
    return validate_input(
        uuid_str,
        "uuid",
        allow_list=AllowLists.UUID,
        required=required
    )


def validate_assessment_type(assessment_type: str) -> ValidationResult:
    """Validate assessment type"""
    return validate_input(
        assessment_type,
        "assessment_type",
        allow_list_set=AllowLists.ASSESSMENT_TYPES,
        required=True
    )


# ============================================================================
# Output Encoding Functions
# ============================================================================

def encode_output(value: Any, sink: OutputSink) -> str:
    """
    Encode output for specific context to prevent injection attacks

    Args:
        value: Value to encode
        sink: Output sink (HTML, JS, CSS, URL, etc.)

    Returns:
        Encoded value safe for the specified context

    Raises:
        ValueError: If sink is not supported
    """

    if value is None:
        return ""

    # Convert to string
    str_value = str(value)

    if sink == OutputSink.HTML:
        return _encode_html(str_value)

    elif sink == OutputSink.HTML_ATTR:
        return _encode_html_attribute(str_value)

    elif sink == OutputSink.JS:
        return _encode_js(str_value)

    elif sink == OutputSink.JS_STRING:
        return _encode_js_string(str_value)

    elif sink == OutputSink.CSS:
        return _encode_css(str_value)

    elif sink == OutputSink.URL:
        return _encode_url(str_value)

    elif sink == OutputSink.SQL:
        raise ValueError(
            "SQL output encoding not supported. "
            "Use parameterized queries instead."
        )

    else:
        raise ValueError(f"Unsupported output sink: {sink}")


def _encode_html(value: str) -> str:
    """Encode for HTML body context"""
    return html.escape(value, quote=True)


def _encode_html_attribute(value: str) -> str:
    """Encode for HTML attribute context"""
    # HTML attribute encoding is more strict
    value = html.escape(value, quote=True)
    # Additionally escape single quotes
    value = value.replace("'", '&#x27;')
    value = value.replace("`", '&#96;')
    return value


def _encode_js(value: str) -> str:
    """Encode for JavaScript context (not inside string)"""
    # This is for when inserting into JS code as an identifier/literal
    # For string contexts, use _encode_js_string
    value = value.replace("\\", "\\\\")
    value = value.replace("'", "\\'")
    value = value.replace('"', '\\"')
    value = value.replace("\n", "\\n")
    value = value.replace("\r", "\\r")
    value = value.replace("\t", "\\t")
    return value


def _encode_js_string(value: str) -> str:
    """Encode for JavaScript string literal context"""
    # Use JSON encoding for JS strings (safest approach)
    try:
        return json.dumps(value)[1:-1]  # Remove quotes
    except (ValueError, TypeError, json.JSONDecodeError) as e:
        # Fallback to manual escaping
        value = value.replace("\\", "\\\\")
        value = value.replace("'", "\\'")
        value = value.replace('"', '\\"')
        value = value.replace("\n", "\\n")
        value = value.replace("\r", "\\r")
        value = value.replace("\t", "\\t")
        return value


def _encode_css(value: str) -> str:
    """Encode for CSS context"""
    # CSS encoding escapes all non-alphanumeric characters
    result = []
    for char in value:
        if char.isalnum():
            result.append(char)
        else:
            # CSS escape: \HH where HH is hex code
            result.append(f"\\{ord(char):02X}")
    return "".join(result)


def _encode_url(value: str) -> str:
    """Encode for URL parameter context"""
    return urllib.parse.quote(value, safe='')


# ============================================================================
# SSRF Prevention
# ============================================================================

class SSRFValidator:
    """Validator to prevent Server-Side Request Forgery attacks"""

    # Blocked internal IP ranges
    BLOCKED_NETWORKS = [
        ip_network('127.0.0.0/8'),  # Loopback
        ip_network('10.0.0.0/8'),   # Private Class A
        ip_network('172.16.0.0/12'),  # Private Class B
        ip_network('192.168.0.0/16'),  # Private Class C
        ip_network('169.254.169.254/32'),  # AWS metadata
        ip_network('0.0.0.0/8'),  # Current network
        ip_network('::1/128'),  # IPv6 loopback
        ip_network('fc00::/7'),  # IPv6 private
        ip_network('fe80::/10'),  # IPv6 link-local
    ]

    # Allowed domains (allow-list approach)
    ALLOWED_DOMAINS = {
        'api.psychsync.com',
        'docs.psychsync.com',
        'www.psychsync.com'
    }

    @classmethod
    def validate_url(cls, url: str) -> ValidationResult:
        """
        Validate URL to prevent SSRF attacks

        Args:
            url: URL to validate

        Returns:
            ValidationResult
        """

        errors = []
        warnings = []

        try:
            # Parse URL
            parsed = urllib.parse.urlparse(url)

            # Check protocol (only HTTP/HTTPS allowed)
            if parsed.scheme not in ['http', 'https']:
                errors.append(f"URL scheme '{parsed.scheme}' not allowed")
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    errors=errors,
                    warnings=warnings,
                    severity=ValidationSeverity.CRITICAL
                )

            # Extract hostname
            hostname = parsed.hostname
            if not hostname:
                errors.append("URL must have a valid hostname")
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    errors=errors,
                    warnings=warnings,
                    severity=ValidationSeverity.ERROR
                )

            # Check if hostname is IP address
            try:
                ip = ip_address(hostname)
                # Check if IP is in blocked range
                for network in cls.BLOCKED_NETWORKS:
                    if ip in network:
                        errors.append(f"URL IP address {ip} is in blocked range")
                        return ValidationResult(
                            is_valid=False,
                            sanitized_value=None,
                            errors=errors,
                            warnings=warnings,
                            severity=ValidationSeverity.CRITICAL
                        )
            except ValueError:
                # Not an IP address, it's a hostname
                # Check against allow-list
                if hostname not in cls.ALLOWED_DOMAINS:
                    errors.append(f"Domain '{hostname}' not in allow-list")
                    warnings.append(
                        f"Allowed domains: {', '.join(sorted(cls.ALLOWED_DOMAINS))}"
                    )
                    return ValidationResult(
                        is_valid=False,
                        sanitized_value=None,
                        errors=errors,
                        warnings=warnings,
                        severity=ValidationSeverity.ERROR
                    )

            # Check for private/internal DNS names
            if hostname.endswith('.local') or hostname.endswith('.internal'):
                errors.append(f"Internal hostname '{hostname}' not allowed")
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    errors=errors,
                    warnings=warnings,
                    severity=ValidationSeverity.CRITICAL
                )

            # Check port
            if parsed.port:
                # Block privileged ports and common internal service ports
                blocked_ports = {22, 23, 25, 53, 135, 137, 138, 139, 445, 3306, 5432, 6379, 27017}
                if parsed.port in blocked_ports:
                    errors.append(f"Port {parsed.port} is blocked")
                    return ValidationResult(
                        is_valid=False,
                        sanitized_value=None,
                        errors=errors,
                        warnings=warnings,
                        severity=ValidationSeverity.ERROR
                    )

            return ValidationResult(
                is_valid=True,
                sanitized_value=url,
                errors=[],
                warnings=[],
                severity=ValidationSeverity.INFO
            )

        except Exception as e:
            errors.append(f"URL parsing failed: {str(e)}")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.ERROR
            )


# ============================================================================
# File Upload Validation
# ============================================================================

class FileUploadValidator:
    """Validator for file uploads to prevent malicious file uploads"""

    # Allowed MIME types
    ALLOWED_MIME_TYPES = {
        'image/jpeg',
        'image/png',
        'image/gif',
        'image/webp',
        'application/pdf',
        'text/plain',
        'text/csv',
        'application/json'
    }

    # Blocked file extensions
    BLOCKED_EXTENSIONS = {
        '.exe', '.bat', '.cmd', '.com', '.scr', '.pif', '.vbs', '.js',
        '.jar', '.sh', '.php', '.asp', '.aspx', .jsp', '.py', '.pl',
        '.rb', '.ps1', '.psm1'
    }

    # Maximum file sizes (bytes)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def validate_file(
        cls,
        filename: str,
        file_content: bytes,
        expected_type: Optional[str] = None
    ) -> ValidationResult:
        """
        Validate uploaded file

        Args:
            filename: Name of the uploaded file
            file_content: File content as bytes
            expected_type: Expected MIME type (optional)

        Returns:
            ValidationResult
        """

        errors = []
        warnings = []

        # Check filename length
        if len(filename) > 255:
            errors.append("Filename too long (max 255 characters)")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.ERROR
            )

        # Check for path traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            errors.append("Filename contains path traversal sequences")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.CRITICAL
            )

        # Check file extension
        _, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        ext = '.' + ext.lower() if ext else ''

        if ext in cls.BLOCKED_EXTENSIONS:
            errors.append(f"File extension '{ext}' is not allowed")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.CRITICAL
            )

        # Check file size
        file_size = len(file_content)
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            max_size = cls.MAX_IMAGE_SIZE
        else:
            max_size = cls.MAX_FILE_SIZE

        if file_size > max_size:
            errors.append(f"File too large (max {max_size // (1024*1024)}MB)")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.ERROR
            )

        # Detect MIME type from content
        mime_type = magic.from_buffer(file_content, mime=True)

        if mime_type not in cls.ALLOWED_MIME_TYPES:
            errors.append(f"File type '{mime_type}' is not allowed")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.ERROR
            )

        # Validate image if it's an image file
        if mime_type.startswith('image/'):
            img_format = imghdr.what(None, h=file_content)
            if img_format is None:
                errors.append("File content does not match a valid image format")
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    errors=errors,
                    warnings=warnings,
                    severity=ValidationSeverity.ERROR
                )

        # Check if expected type matches
        if expected_type and mime_type != expected_type:
            errors.append(f"File type mismatch: expected {expected_type}, got {mime_type}")
            return ValidationResult(
                is_valid=False,
                sanitized_value=None,
                errors=errors,
                warnings=warnings,
                severity=ValidationSeverity.ERROR
            )

        # Generate safe filename
        safe_filename = cls._sanitize_filename(filename)

        return ValidationResult(
            is_valid=True,
            sanitized_value=safe_filename,
            errors=[],
            warnings=[f"File validated successfully: {mime_type}"],
            severity=ValidationSeverity.INFO
        )

    @classmethod
    def _sanitize_filename(cls, filename: str) -> str:
        """Generate safe filename"""
        # Remove directory paths
        filename = filename.split('/')[-1].split('\\')[-1]

        # Remove special characters, keep alphanumeric, hyphen, underscore, dot
        filename = re.sub(r'[^\w.-]', '_', filename)

        # Add hash to prevent collisions
        hash_suffix = hashlib.sha256(filename.encode()).hexdigest()[:8]
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        safe_filename = f"{name}_{hash_suffix}.{ext}" if ext else f"{name}_{hash_suffix}"

        return safe_filename


# ============================================================================
# SQL Injection Prevention (Parameterized Query Enforcement)
# ============================================================================

class SQLValidator:
    """Validator to ensure parameterized queries are used"""

    @classmethod
    def validate_query_safe(cls, query: str) -> ValidationResult:
        """
        Validate that SQL query is safe (parameterized)

        Note: This is a basic check. Always use proper ORM/parameterized queries.

        Args:
            query: SQL query to validate

        Returns:
            ValidationResult
        """

        errors = []
        warnings = []

        # Check for string concatenation patterns (dangerous)
        dangerous_patterns = [
            (r'f["\'].*SELECT.*\{.*\}', 'String formatting in query'),
            (r'f["\'].*INSERT.*\{.*\}', 'String formatting in query'),
            (r'["\'][^"\']*\'\s*\+', 'String concatenation in query'),
            (r'\$\w+', 'Unescaped variable in query'),
        ]

        for pattern, description in dangerous_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                errors.append(f"Query contains dangerous pattern: {description}")
                return ValidationResult(
                    is_valid=False,
                    sanitized_value=None,
                    errors=errors,
                    warnings=warnings,
                    severity=ValidationSeverity.CRITICAL
                )

        # Check for proper parameter placeholder patterns
        # SQLAlchemy style: :param
        # psycopg2 style: %s
        # SQLite style: ?
        has_params = bool(
            re.search(r':\w+', query) or  # SQLAlchemy
            re.search(r'%s', query) or    # psycopg2
            re.search(r'\?', query)       # SQLite
        )

        if has_params or 'SELECT' not in query.upper():
            return ValidationResult(
                is_valid=True,
                sanitized_value=query,
                errors=[],
                warnings=[],
                severity=ValidationSeverity.INFO
            )

        warnings.append("Query may not be using parameters")

        return ValidationResult(
            is_valid=True,
            sanitized_value=query,
            errors=[],
            warnings=warnings,
            severity=ValidationSeverity.WARNING
        )


# ============================================================================
# Comprehensive Validation Function
# ============================================================================

def validate_and_encode(
    value: Any,
    field_name: str,
    input_constraints: Optional[Dict[str, Any]] = None,
    output_sink: Optional[OutputSink] = None
) -> ValidationResult:
    """
    Combined validation and encoding function

    Args:
        value: Input value
        field_name: Field name for error messages
        input_constraints: Dict of validation constraints
        output_sink: Output sink for encoding

    Returns:
        ValidationResult with sanitized and encoded value
    """

    # Validate input
    if input_constraints:
        result = validate_input(value, field_name, **input_constraints)
    else:
        result = ValidationResult(
            is_valid=True,
            sanitized_value=value,
            errors=[],
            warnings=[],
            severity=ValidationSeverity.INFO
        )

    # Encode output if requested and validation passed
    if result.is_valid and output_sink and result.sanitized_value is not None:
        try:
            encoded = encode_output(result.sanitized_value, output_sink)
            result.sanitized_value = encoded
        except Exception as e:
            result.errors.append(f"Output encoding failed: {str(e)}")
            result.is_valid = False
            result.severity = ValidationSeverity.ERROR

    return result
