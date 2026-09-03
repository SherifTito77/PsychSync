"""
Database-agnostic type definitions for cross-platform compatibility

This module provides types that work across different database backends:
- PostgreSQL: Uses optimized types like JSONB
- SQLite: Falls back to compatible types
- MySQL/MariaDB: Uses appropriate types

Import these types instead of database-specific types to maintain portability.
"""

import uuid

from sqlalchemy import JSON as _JSON
from sqlalchemy import TIMESTAMP, String, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID


class GUID(TypeDecorator):
    """
    Platform-independent GUID type.

    Uses PostgreSQL's UUID type when available, otherwise uses String(36).
    """

    impl = String
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID())
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(value)


# Re-export for convenience
__all__ = [
    "TIMESTAMP",
    "JSONType",  # Cross-database JSON type
    "JSON",
    "GUID",  # Cross-database GUID type
    "UUID",  # PostgreSQL UUID (for legacy compatibility)
    "JSONB",  # For PostgreSQL-only code (not recommended)
    "ARRAY",  # Added for compatibility
]

# Alias for backward compatibility
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

UUID = PG_UUID

# ...


class JSONType(_JSON):
    """
    Cross-database JSON type that uses the best implementation for each database.

    - PostgreSQL: Uses JSONB (binary, indexed, faster)
    - SQLite: Uses JSON (stored as TEXT with JSON operations)
    - MySQL: Uses JSON type

    This ensures tests can run on SQLite while production uses PostgreSQL.

    Note: PostgreSQL-specific parameters like `astext_type` are accepted but ignored
    on non-PostgreSQL databases for compatibility.
    """

    inherit_cache = True

    def __init__(self, *args, **kwargs):
        """
        Initialize with filtering of PostgreSQL-specific parameters.

        Removes/ignores PostgreSQL-specific parameters when using other dialects.
        """
        # Extract PostgreSQL-specific parameters
        pg_specific_params = ["astext_type", "none_as_null"]
        filtered_kwargs = {
            k: v for k, v in kwargs.items() if k not in pg_specific_params
        }

        super().__init__(*args, **filtered_kwargs)


# For backward compatibility during migration
JSON = JSONType
JSONB = JSONType  # Alias to allow gradual migration
ARRAY = JSONType  # Alias ARRAY to JSONType for compatibility


def __getattr__(name: str):
    """Provide helpful error message for deprecated imports"""
    if name == "JSONB":
        import warnings

        warnings.warn(
            "Direct JSONB import is deprecated. Use JSONType for cross-database compatibility. "
            "JSONB is now an alias for JSONType.",
            DeprecationWarning,
            stacklevel=2,
        )
        return JSONType
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
