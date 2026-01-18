"""
Unified Security Middleware Package

A modular, composable security middleware system that consolidates
all duplicate security implementations into a single, coherent system.

This package replaces:
- app/middleware/security.py (571 lines)
- app/middleware/security_middleware.py (441 lines)
- app/middleware/enterprise_security_middleware.py
- app/middleware/comprehensive_security_headers.py
- app/middleware/security_headers.py
- app/middleware/csrf_xss_protection.py
- app/core/security_advanced.py (SecurityMiddleware)
- app/core/security_middleware.py

Usage:
    from app.middleware.security_unified import UnifiedSecurityMiddleware, SecurityConfig

    config = SecurityConfig(
        csrf_protection_enabled=True,
        ip_blocking_enabled=True,
        csp_level="high",
    )
    app.add_middleware(UnifiedSecurityMiddleware, config=config)
"""

from app.middleware.security_unified.middleware import (
    UnifiedSecurityMiddleware,
    SecurityConfig,
)

from app.middleware.security_unified.utils import (
    get_client_ip,
    get_client_info,
    detect_attack_tool,
    is_suspicious_path,
    is_sensitive_endpoint,
    get_security_headers_default,
    get_csp_template,
)

__all__ = [
    "UnifiedSecurityMiddleware",
    "SecurityConfig",
    "get_client_ip",
    "get_client_info",
    "detect_attack_tool",
    "is_suspicious_path",
    "is_sensitive_endpoint",
    "get_security_headers_default",
    "get_csp_template",
]
