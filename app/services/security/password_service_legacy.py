"""
Legacy password service adapter.
Provides access to password history check and other legacy utilities.
"""

from app.core.security import (
    validate_password,
    _contains_common_words as core_contains,
    _get_strength_rating as core_get_strength,
    get_password_hash as core_hash_password,
    verify_password as core_verify_password,
)


async def check_password_history(db, user_id, password):
    # This is a legacy stub.
    return False


def validate_password_strength(password):
    result = validate_password(password)
    return result["valid"]


def hash_password(password):
    return core_hash_password(password)


def verify_password(password, hashed):
    return core_verify_password(password, hashed)


def _contains_common_words(password: str) -> bool:
    return core_contains(password)


def _get_strength_rating(score: int) -> str:
    return core_get_strength(score)
