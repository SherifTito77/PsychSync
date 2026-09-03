"""
Dynamic Security Headers Configuration
Provides secure headers with dynamic host configuration
"""

import logging

from fastapi import Request, Response

logger = logging.getLogger(__name__)


def get_dynamic_security_headers(request: Request) -> dict:
    """
    Generate security headers with dynamic host configuration

    Args:
        request: FastAPI request object

    Returns:
        Dictionary of security headers
    """
    # Get the current host and protocol
    host = request.headers.get("host", "localhost")
    protocol = "https" if request.url.scheme == "https" else "http"

    # Build dynamic CSP connect sources
    connect_sources = [
        "'self'",
        f"{protocol}://{host}",
        f"wss://{host}" if protocol == "https" else f"ws://{host}",
    ]

    # In development, allow localhost connections
    if host in ["localhost", "127.0.0.1"] or "localhost" in host:
        connect_sources.extend(
            [
                "ws://localhost:8000",
                "ws://localhost:3000",
                "ws://localhost:5173",
                "ws://localhost:5174",
                "http://localhost:8000",
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:5174",
                "https://localhost:8443",
            ]
        )

    # Build CSP header
    csp_value = (
        f"default-src 'self'; "
        f"script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
        f"style-src 'self' 'unsafe-inline'; "
        f"img-src 'self' data: https:; "
        f"font-src 'self' data:; "
        f"connect-src {' '.join(connect_sources)}; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'; "
        f"upgrade-insecure-requests;"
    )

    # Build security headers
    headers = {
        # Clickjacking protection
        "X-Frame-Options": "DENY",
        # MIME type sniffing protection
        "X-Content-Type-Options": "nosniff",
        # XSS protection
        "X-XSS-Protection": "1; mode=block",
        # Referrer policy
        "Referrer-Policy": "strict-origin-when-cross-origin",
        # Content Security Policy
        "Content-Security-Policy": csp_value,
        # HSTS (only on HTTPS)
        "Strict-Transport-Security": (
            "max-age=31536000; includeSubDomains; preload"
            if protocol == "https"
            else ""
        ),
        # Permissions policy
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
        # Cross-domain policies
        "X-Permitted-Cross-Domain-Policies": "none",
        # DNS prefetch control
        "X-DNS-Prefetch-Control": "off",
        # Cross-origin embedder policy
        "Cross-Origin-Embedder-Policy": "require-corp",
        # Cross-origin opener policy
        "Cross-Origin-Opener-Policy": "same-origin",
        # CSRF protection
        "X-CSRF-Protection": "1; mode=strict",
    }

    # Remove empty headers
    headers = {k: v for k, v in headers.items() if v}

    logger.debug(f"Generated security headers for host: {host}")
    return headers


def add_security_headers(response: Response, request: Request) -> Response:
    """
    Add security headers to response

    Args:
        response: FastAPI response object
        request: FastAPI request object

    Returns:
        Response with security headers added
    """
    headers = get_dynamic_security_headers(request)

    for header_name, header_value in headers.items():
        response.headers[header_name] = header_value

    logger.debug(f"Added {len(headers)} security headers to response")
    return response
