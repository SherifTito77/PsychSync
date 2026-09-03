# app/services/security/utils.py
import hashlib
import hmac
import secrets


def constant_time_compare(val1: str, val2: str) -> bool:
    """Compare two strings in constant time to prevent timing attacks."""
    return hmac.compare_digest(val1.encode(), val2.encode())


def hash_string(data: str, salt: str = "") -> str:
    """Hash a string using SHA-256."""
    return hashlib.sha256((data + salt).encode()).hexdigest()
