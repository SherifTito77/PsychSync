
# app/services/auth_service.py
from app.core.security import create_access_token, verify_password, get_password_hash


# Token blacklist (in production, use Redis)
_token_blacklist = set()

def blacklist_token(token: str, expiry: datetime = None) -> None:
    """
    Add token to blacklist

    Args:
        token: Token to blacklist
        expiry: Optional expiry time for auto-cleanup
    """
    _token_blacklist.add(token)

    # In production, use Redis with TTL:
    # redis.setex(f"blacklist:{token}", int(expiry.timestamp() - datetime.now().timestamp()), "1")

def is_token_blacklisted(token: str) -> bool:
    """
    Check if token is blacklisted

    Args:
        token: Token to check

    Returns:
        True if blacklisted
    """
    return token in _token_blacklist
    # In production:
    # return redis.exists(f"blacklist:{token}")


