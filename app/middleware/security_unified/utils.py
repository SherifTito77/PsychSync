"""
Unified Security Utilities

Common utility functions shared across all security middleware features.
This eliminates duplication and ensures consistent behavior.
"""

import ipaddress
import logging
from typing import Any

from fastapi import Request

logger = logging.getLogger(__name__)


def get_client_ip(request: Request) -> str:
    """
    Extract client IP address from request, handling proxy headers.

    This is the SINGLE source of truth for IP extraction across all security middleware.
    Duplicated in 14+ files previously - now consolidated here.

    Args:
        request: FastAPI request object

    Returns:
        Client IP address as string

    Security considerations:
        - Checks X-Forwarded-For header (set by reverse proxies)
        - Checks X-Real-IP header (set by Nginx/Apache)
        - Falls back to direct connection IP
        - Handles comma-separated IPs in X-Forwarded-For (takes first)
        - Returns "unknown" if no IP can be determined
    """
    # Check for X-Forwarded-For header (set by load balancers/proxies)
    # Format: "X-Forwarded-For: client, proxy1, proxy2"
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        client_ip = forwarded_for.split(",")[0].strip()
        # Validate it's a valid IP
        try:
            ipaddress.ip_address(client_ip)
            return client_ip
        except ValueError:
            logger.warning(f"Invalid IP in X-Forwarded-For: {client_ip}")

    # Check for X-Real-IP header (set by Nginx/Apache)
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        try:
            ipaddress.ip_address(real_ip)
            return real_ip
        except ValueError:
            logger.warning(f"Invalid IP in X-Real-IP: {real_ip}")

    # Check CF-Connecting-IP (Cloudflare)
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        try:
            ipaddress.ip_address(cf_ip)
            return cf_ip
        except ValueError:
            logger.warning(f"Invalid IP in CF-Connecting-IP: {cf_ip}")

    # Fall back to direct connection IP
    if request.client and request.client.host:
        try:
            ipaddress.ip_address(request.client.host)
            return request.client.host
        except ValueError:
            logger.warning(f"Invalid direct connection IP: {request.client.host}")

    # Unable to determine IP
    logger.debug("Unable to determine client IP")
    return "unknown"


def get_client_info(request: Request) -> dict[str, Any]:
    """
    Extract comprehensive client information from request.

    Args:
        request: FastAPI request object

    Returns:
        Dictionary with client information (IP, user agent, etc.)
    """
    return {
        "ip": get_client_ip(request),
        "user_agent": request.headers.get("User-Agent", "unknown"),
        "referer": request.headers.get("Referer", ""),
        "method": request.method,
        "path": request.url.path,
        "query_params": str(request.query_params),
        "headers": dict(request.headers),
    }


def is_private_ip(ip_str: str) -> bool:
    """
    Check if IP address is in private range.

    Args:
        ip_str: IP address string

    Returns:
        True if IP is private (RFC 1918, RFC 4193, or localhost)
    """
    try:
        ip = ipaddress.ip_address(ip_str)
        return ip.is_private or ip.is_loopback or ip.is_link_local
    except ValueError:
        return False


def sanitize_user_agent(user_agent: str | None) -> str:
    """
    Sanitize user agent string for logging.

    Args:
        user_agent: Raw user agent string

    Returns:
        Sanitized user agent (truncated if too long)
    """
    if not user_agent:
        return "unknown"

    # Limit length to prevent log injection
    max_length = 500
    if len(user_agent) > max_length:
        return user_agent[:max_length] + "..."

    return user_agent


def extract_request_fingerprint(request: Request) -> str:
    """
    Generate a fingerprint of the request for tracking/analysis.

    Uses multiple factors to identify unique requests/clients:
    - IP address
    - User-Agent
    - Accept headers
    - Accept-Encoding
    - Accept-Language

    Args:
        request: FastAPI request object

    Returns:
        Fingerprint hash (string)
    """
    import hashlib

    factors = [
        get_client_ip(request),
        request.headers.get("User-Agent", ""),
        request.headers.get("Accept", ""),
        request.headers.get("Accept-Encoding", ""),
        request.headers.get("Accept-Language", ""),
    ]

    fingerprint_string = "|".join(factors)
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]


def is_sensitive_endpoint(path: str) -> bool:
    """
    Check if the endpoint path is security-sensitive.

    Sensitive endpoints require additional security measures:
    - Stricter rate limiting
    - No caching
    - Enhanced logging
    - CSRF validation

    Args:
        path: Request path

    Returns:
        True if endpoint is sensitive
    """
    sensitive_patterns = [
        "/api/v1/auth/",
        "/api/v1/users/",
        "/api/v1/admin/",
        "/api/v1/password/",
        "/api/v1/settings/",
        "/auth/",
        "/login",
        "/register",
        "/reset",
    ]

    path_lower = path.lower()
    return any(pattern.lower() in path_lower for pattern in sensitive_patterns)


def get_security_headers_default() -> dict[str, str]:
    """
    Get default security headers according to OWASP guidelines.

    Returns:
        Dictionary of header name -> value
    """
    return {
        # Prevents MIME-sniffing
        "X-Content-Type-Options": "nosniff",

        # Prevents clickjacking (legacy, CSP frame-ancestors preferred)
        "X-Frame-Options": "DENY",

        # Enables browser XSS filter (legacy, modern browsers ignore)
        "X-XSS-Protection": "1; mode=block",

        # Controls referrer information leakage
        "Referrer-Policy": "strict-origin-when-cross-origin",

        # Controls cross-origin window access
        "Cross-Origin-Opener-Policy": "same-origin",

        # Controls cross-origin resource access
        "Cross-Origin-Resource-Policy": "same-origin",

        # Controls browser features and APIs
        "Permissions-Policy": (
            "geolocation=(), "
            "microphone=(), "
            "camera=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "gyroscope=(), "
            "accelerometer=()"
        ),
    }


def get_csp_template(level: str = "medium") -> str:
    """
    Get Content-Security-Policy template by security level.

    Args:
        level: Security level (low, medium, high, strict)

    Returns:
        CSP header value string
    """
    templates = {
        "low": (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: blob: https://fastapi.tiangolo.com; "
            "connect-src 'self' ws://localhost:* wss://localhost:* https://api.stripe.com;"
        ),
        "medium": (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https: https://fastapi.tiangolo.com; "
            "connect-src 'self' ws://localhost:* wss://localhost:*; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        ),
        "high": (
            "default-src 'self'; "
            "script-src 'self' https://cdn.jsdelivr.net; "
            "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self'; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self' wss://localhost:*; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests;"
        ),
        "strict": (
            "default-src 'self'; "
            "script-src 'self' 'nonce-{nonce}' https://cdn.jsdelivr.net; "
            "style-src 'self' 'nonce-{nonce}' https://fonts.googleapis.com https://cdn.jsdelivr.net; "
            "font-src 'self'; "
            "img-src 'self' data: https://fastapi.tiangolo.com; "
            "connect-src 'self' wss://localhost:*; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none'; "
            "upgrade-insecure-requests; "
            "form-action 'self';"
        ),
    }

    return templates.get(level.lower(), templates["medium"])


# Attack tool signatures for detection
ATTACK_TOOL_SIGNATURES = {
    "sqlmap": ["sqlmap", "sql map"],
    "nikto": ["nikto"],
    "nmap": ["nmap", "nmap scripting"],
    "masscan": ["masscan"],
    "dirb": ["dirb", "dirbuster"],
    "gobuster": ["gobuster"],
    "burp": ["burp suite", "burp collaborator"],
    "zap": ["owasp zap", "zap spider"],
    "w3af": ["w3af"],
    "hydra": ["thc-hydra", "hydra ftp"],
    "metasploit": ["metasploit", "msfconsole"],
}


def detect_attack_tool(user_agent: str | None) -> str | None:
    """
    Detect if request is from a known security testing tool.

    Args:
        user_agent: User-Agent header value

    Returns:
        Tool name if detected, None otherwise
    """
    if not user_agent:
        return None

    user_agent_lower = user_agent.lower()

    for tool_name, signatures in ATTACK_TOOL_SIGNATURES.items():
        for signature in signatures:
            if signature in user_agent_lower:
                return tool_name

    return None


def is_suspicious_path(path: str) -> bool:
    """
    Check if request path looks suspicious (common attack patterns).

    Args:
        path: Request path

    Returns:
        True if path matches suspicious patterns
    """
    import re

    suspicious_patterns = [
        r"\.\./",  # Path traversal
        r"<script",  # XSS attempt
        r"javascript:",  # XSS attempt
        r"union\s+select",  # SQL injection
        r"eval\s*\(",  # Code injection
        r"document\.cookie",  # Cookie theft
        r"/etc/passwd",  # File inclusion
        r"cmd\.exe",  # Command injection
        r"\.\.\\",  # Windows path traversal
    ]

    path_lower = path.lower()
    for pattern in suspicious_patterns:
        if re.search(pattern, path_lower, re.IGNORECASE):
            return True

    return False
