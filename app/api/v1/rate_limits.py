"""
Rate limiting decorators for API endpoints.

This module provides rate limiting decorators using slowapi.
Separated from main.py to avoid circular imports.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from fastapi import Request

# Initialize rate limiter with IP-based key function
limiter = Limiter(key_func=get_remote_address)

# Export the limiter for use in endpoints
__all__ = ["limiter"]
