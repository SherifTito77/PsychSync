# app/core/security_utils.py
"""
Security utilities for input sanitization and XSS protection
"""

import html
import logging
import re
from typing import Any

# Try to import bleach, fallback to basic sanitization if not available
try:
    from bleach import clean
    from bleach.css_sanitizer import CSSSanitizer

    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

logger = logging.getLogger(__name__)

# Configure allowed HTML tags and attributes
ALLOWED_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "u",
    "i",
    "b",
    "ul",
    "ol",
    "li",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "blockquote",
    "code",
    "pre",
]

ALLOWED_ATTRIBUTES = {
    "*": ["class"],
    "a": ["href", "title"],
    "img": ["src", "alt", "width", "height"],
}

# CSS sanitizer for style attributes (only if bleach is available)
css_sanitizer = (
    CSSSanitizer(
        allowed_css_properties=[
            "color",
            "background-color",
            "font-size",
            "font-weight",
            "text-align",
            "margin",
            "padding",
            "border",
            "display",
        ]
    )
    if BLEACH_AVAILABLE
    else None
)


def sanitize_html(input_value: str, allowed_tags: list[str] = None) -> str:
    """
    Sanitize HTML input to prevent XSS attacks

    Args:
        input_value: The input string to sanitize
        allowed_tags: List of allowed HTML tags (defaults to safe tags)

    Returns:
        Sanitized string with dangerous HTML removed
    """
    if not isinstance(input_value, str):
        return str(input_value)

    if not input_value.strip():
        return ""

    try:
        if BLEACH_AVAILABLE:
            tags = allowed_tags if allowed_tags is not None else []

            # Use bleach to sanitize HTML
            sanitized = clean(
                input_value,
                tags=tags,
                attributes=ALLOWED_ATTRIBUTES,
                css_sanitizer=css_sanitizer,
                strip=True,
            )
        else:
            # Basic HTML sanitization without bleach
            # Remove script tags and dangerous attributes
            sanitized = re.sub(
                r"<script[^>]*>.*?</script>", "", input_value, flags=re.IGNORECASE | re.DOTALL
            )
            sanitized = re.sub(
                r"<iframe[^>]*>.*?</iframe>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
            )
            sanitized = re.sub(
                r"<object[^>]*>.*?</object>", "", sanitized, flags=re.IGNORECASE | re.DOTALL
            )
            sanitized = re.sub(r"<embed[^>]*>", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"<link[^>]*>", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"<meta[^>]*>", "", sanitized, flags=re.IGNORECASE)

            # Remove dangerous attributes
            sanitized = re.sub(r'on\w+\s*=\s*["\'][^"\']*["\']', "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"javascript\s*:", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"vbscript\s*:", "", sanitized, flags=re.IGNORECASE)
            sanitized = re.sub(r"data\s*:", "", sanitized, flags=re.IGNORECASE)

        # Additional regex patterns for edge cases
        sanitized = re.sub(r"javascript\s*:", "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"vbscript\s*:", "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"on\w+\s*=", "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    except Exception as e:
        logger.error(f"Error sanitizing HTML: {e}")
        # Fallback to basic HTML escaping
        return html.escape(input_value, quote=True)


def sanitize_string(input_value: str | Any) -> str:
    """
    Sanitize string input by removing all HTML tags

    Args:
        input_value: The input value to sanitize

    Returns:
        Plain text string with all HTML removed
    """
    if not isinstance(input_value, str):
        return str(input_value)

    if not input_value.strip():
        return ""

    try:
        if BLEACH_AVAILABLE:
            # Remove all HTML tags using bleach
            sanitized = clean(input_value, tags=[], strip=True)
        else:
            # Basic HTML tag removal without bleach
            sanitized = re.sub(r"<[^>]+>", "", input_value)

        # Remove any remaining potentially dangerous content
        sanitized = re.sub(r"javascript\s*:", "", sanitized, flags=re.IGNORECASE)

        sanitized = re.sub(r"vbscript\s*:", "", sanitized, flags=re.IGNORECASE)

        return sanitized.strip()

    except Exception as e:
        logger.error(f"Error sanitizing string: {e}")
        return html.escape(input_value, quote=True)


def sanitize_dict(
    input_dict: dict[str, Any], html_fields: list[str] = None, text_fields: list[str] = None
) -> dict[str, Any]:
    """
    Sanitize a dictionary of input values

    Args:
        input_dict: Dictionary to sanitize
        html_fields: List of field names that allow safe HTML
        text_fields: List of field names that should be plain text

    Returns:
        Sanitized dictionary
    """
    if not isinstance(input_dict, dict):
        return input_dict

    sanitized = {}
    html_fields = html_fields or []
    text_fields = text_fields or []

    for key, value in input_dict.items():
        if isinstance(value, str):
            if key in html_fields:
                sanitized[key] = sanitize_html(value)
            else:
                sanitized[key] = sanitize_string(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value, html_fields, text_fields)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_html(item)
                if isinstance(item, str) and key in html_fields
                else sanitize_string(item)
                if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized


def validate_email(email: str) -> bool:
    """
    Validate email format

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(email, str):
        return False

    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return re.match(email_pattern, email.strip()) is not None


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format

    Args:
        uuid_string: UUID string to validate

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(uuid_string, str):
        return False

    uuid_pattern = r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
    return re.match(uuid_pattern, uuid_string.strip()) is not None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent directory traversal attacks

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename
    """
    if not isinstance(filename, str):
        return ""

    # Remove directory traversal attempts
    sanitized = filename.replace("..", "").replace("/", "").replace("\\", "")

    # Remove null bytes
    sanitized = sanitized.replace("\x00", "")

    # Remove control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", sanitized)

    # Limit length
    sanitized = sanitized[:255]

    return sanitized.strip()


# Security headers configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


def get_security_headers() -> dict[str, str]:
    """
    Get security headers for HTTP responses

    Returns:
        Dictionary of security headers
    """
    return SECURITY_HEADERS.copy()
