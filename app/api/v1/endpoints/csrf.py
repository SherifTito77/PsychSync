# app/api/v1/endpoints/csrf.py
"""
CSRF Token Endpoint for API Protection
"""
from fastapi import APIRouter, Response
import secrets

router = APIRouter()

@router.get("/token")
async def get_csrf_token():
    """
    Get a CSRF token for use in API requests

    Returns a secure CSRF token that should be included in:
    - Header: X-CSRF-Token
    - Or as form field: csrf_token (for form submissions)
    """
    # Generate a secure random token
    csrf_token = secrets.token_urlsafe(32)

    return {"csrf_token": csrf_token}