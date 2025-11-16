# app/db/models/__init__.py

# Import only essential models for testing authentication
from .user import User

# Make models available when importing from this package
__all__ = [
    "User",
]