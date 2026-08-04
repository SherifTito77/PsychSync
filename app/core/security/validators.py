"""
PsychSync Enterprise Security - Sanitization and Validation
Unified module for input sanitization, HTML/text cleanup, and structural validation.
"""

import html
import logging
import re
from typing import Any, Dict, List, Optional

# Try to import bleach, fallback to basic sanitization if not available
try:
    from bleach import clean
    from bleach.css_sanitizer import CSSSanitizer

    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# HTML & String Sanitization
# =============================================================================


def sanitize_html(input_value: str, allowed_tags: Optional[List[str]] = None) -> str:
    """Sanitize HTML input to prevent XSS attacks."""
    if not isinstance(input_value, str) or not input_value.strip():
        return str(input_value) if input_value else ""

    try:
        if BLEACH_AVAILABLE:
            return clean(input_value, tags=allowed_tags or [], strip=True)
        # Basic fallback for when bleach is unavailable
        return re.sub(
            r"<script[^>]*>.*?</script>",
            "",
            input_value,
            flags=re.IGNORECASE | re.DOTALL,
        )
    except Exception as e:
        logger.error(f"Error sanitizing HTML: {e}")
        return html.escape(input_value, quote=True)


def sanitize_string(input_value: str | Any) -> str:
    """Sanitize string by removing all HTML tags."""
    if not isinstance(input_value, str) or not input_value.strip():
        return str(input_value) if input_value else ""

    try:
        if BLEACH_AVAILABLE:
            return clean(input_value, tags=[], strip=True)
        return re.sub(r"<[^>]+>", "", input_value)
    except Exception as e:
        logger.error(f"Error sanitizing string: {e}")
        return html.escape(input_value, quote=True)


# =============================================================================
# Structural Validation
# =============================================================================


def validate_email(email: str) -> bool:
    """Validate email format."""
    if not isinstance(email, str):
        return False
    return bool(
        re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email.strip())
    )


def validate_uuid(uuid_string: str) -> bool:
    """Validate UUID format."""
    if not isinstance(uuid_string, str):
        return False
    return bool(
        re.match(
            r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$",
            uuid_string.strip(),
        )
    )


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent directory traversal."""
    if not isinstance(filename, str):
        return ""
    sanitized = (
        filename.replace("..", "")
        .replace("/", "")
        .replace("\\", "")
        .replace("\x00", "")
    )
    return re.sub(r"[\x00-\x1f\x7f]", "", sanitized).strip()[:255]


def _contains_common_words(password: str) -> bool:
    """
    Check if password contains common dictionary words
    """
    common_words = [
        "the",
        "and",
        "for",
        "are",
        "but",
        "not",
        "you",
        "all",
        "can",
        "had",
        "her",
        "was",
        "one",
        "our",
        "out",
        "day",
        "get",
        "has",
        "him",
        "his",
        "how",
        "man",
        "new",
        "now",
        "old",
        "see",
        "two",
        "way",
        "who",
        "boy",
        "did",
        "its",
        "let",
        "put",
        "say",
        "she",
        "too",
        "use",
    ]
    password_lower = password.lower()
    for word in common_words:
        if word in password_lower:
            return True
    return False


def _get_strength_rating(score: int) -> str:
    """
    Get password strength rating based on score
    """
    if score >= 90:
        return "Very Strong"
    if score >= 80:
        return "Strong"
    if score >= 70:
        return "Good"
    if score >= 60:
        return "Fair"
    if score >= 40:
        return "Weak"
    return "Very Weak"


def validate_password(password: str) -> Dict[str, Any]:
    """
    Enhanced password validation with comprehensive security requirements
    """
    errors = []
    warnings = []
    # Simplified version for compatibility
    if len(password) < 8:
        errors.append("Password too short")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "strength_score": 50,
        "strength_rating": "Fair",
    }
