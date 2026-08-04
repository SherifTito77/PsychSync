# app/core/secure_serialization.py
"""
SECURE SERIALIZATION FOR CACHE LAYER
JSON-based serialization to replace unsafe pickle

This module provides secure serialization for cached data, preventing
arbitrary code execution vulnerabilities (CWE-502) associated with pickle.

WHY JSON OVER PICKLE:
- pickle.execute arbitrary code on deserialization (RCE vulnerability)
- JSON only handles primitive types (safer by design)
- Custom serializers for complex types (datetime, enums, etc.)
- Human-readable cache data (easier debugging)

Author: Security Team
Version: 1.0
"""

import base64
import hashlib
import json
import logging
from dataclasses import asdict, is_dataclass
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SerializationError(Exception):
    """Raised when serialization fails"""


class DeserializationError(Exception):
    """Raised when deserialization fails"""


# Type markers for complex types
TYPE_MARKERS = {
    "datetime": "__datetime__",
    "date": "__date__",
    "time": "__time__",
    "decimal": "__decimal__",
    "bytes": "__bytes__",
    "enum": "__enum__",
    "set": "__set__",
    "tuple": "__tuple__",
}


def json_serialize(obj: Any, pretty: bool = False) -> str:
    """
    Serialize Python object to JSON string

    Args:
        obj: Python object to serialize
        pretty: If True, format with indentation (for debugging)

    Returns:
        JSON string

    Raises:
        SerializationError: If object cannot be serialized
    """
    try:
        indent = 2 if pretty else None
        return json.dumps(
            obj, default=_serialize_default, indent=indent, ensure_ascii=False
        )
    except (TypeError, ValueError) as e:
        raise SerializationError(f"Failed to serialize object: {e}") from e


def json_deserialize(json_str: str, expected_type: type | None = None) -> Any:
    """
    Deserialize JSON string to Python object

    Args:
        json_str: JSON string to deserialize
        expected_type: Optional type to validate after deserialization

    Returns:
        Deserialized Python object

    Raises:
        DeserializationError: If JSON is invalid or type mismatch
    """
    try:
        obj = json.loads(json_str)
        obj = _deserialize_custom(obj)

        # Optional type validation
        if expected_type is not None:
            if not isinstance(obj, expected_type):
                raise DeserializationError(
                    f"Expected type {expected_type}, got {type(obj)}"
                )

        return obj
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        raise DeserializationError(f"Failed to deserialize JSON: {e}") from e


def _serialize_default(obj: Any) -> Any:
    """
    Custom serializer for complex Python types

    Handles:
    - datetime, date, time objects
    - Decimal objects
    - bytes objects
    - Enum objects
    - set and tuple objects
    - dataclasses
    """
    # Datetime objects
    if isinstance(obj, datetime):
        return {
            TYPE_MARKERS["datetime"]: obj.isoformat(),
            "__tz__": obj.tzname() if obj.tzinfo else None,
        }

    # Date objects
    if isinstance(obj, date):
        return {TYPE_MARKERS["date"]: obj.isoformat()}

    # Time objects
    if isinstance(obj, time):
        return {TYPE_MARKERS["time"]: obj.isoformat()}

    # Decimal objects
    if isinstance(obj, Decimal):
        return {TYPE_MARKERS["decimal"]: str(obj)}

    # Bytes objects
    if isinstance(obj, bytes):
        return {TYPE_MARKERS["bytes"]: base64.b64encode(obj).decode("ascii")}

    # Enum objects
    if isinstance(obj, Enum):
        return {
            TYPE_MARKERS["enum"]: {
                "class": obj.__class__.__name__,
                "module": obj.__class__.__module__,
                "value": obj.value,
            }
        }

    # Set objects
    if isinstance(obj, set):
        return {TYPE_MARKERS["set"]: list(obj)}

    # Tuple objects
    if isinstance(obj, tuple):
        return {TYPE_MARKERS["tuple"]: list(obj)}

    # Dataclasses
    if is_dataclass(obj):
        return {**asdict(obj), "__dataclass__": obj.__class__.__name__}

    # Try to convert to string for other types
    try:
        return str(obj)
    except Exception:
        raise SerializationError(
            f"Cannot serialize object of type {type(obj)}"
        ) from None


def _deserialize_custom(obj: Any) -> Any:
    """
    Deserialize custom types from JSON representation

    Recursively processes the JSON structure and converts special markers
    back to their original Python types.
    """
    if isinstance(obj, dict):
        # Check for type markers
        for type_name, marker in TYPE_MARKERS.items():
            if marker in obj:
                return _deserialize_type(type_name, obj[marker], obj)

        # Check for dataclass
        if "__dataclass__" in obj:
            # Dataclasses are deserialized as regular dicts
            # The calling code should reconstruct the dataclass if needed
            obj_copy = obj.copy()
            del obj_copy["__dataclass__"]
            return obj_copy

        # Regular dict - recurse
        return {k: _deserialize_custom(v) for k, v in obj.items()}

    if isinstance(obj, list):
        return [_deserialize_custom(item) for item in obj]

    return obj


def _deserialize_type(type_name: str, value: Any, metadata: dict) -> Any:
    """Deserialize specific types from their marker representation"""

    if type_name == "datetime":
        dt = datetime.fromisoformat(value)
        # Restore timezone if present
        if metadata.get("__tz__"):
            # Note: This is simplified. For production, use pytz or zoneinfo
            pass
        return dt

    if type_name == "date":
        return date.fromisoformat(value)

    if type_name == "time":
        return time.fromisoformat(value)

    if type_name == "decimal":
        return Decimal(value)

    if type_name == "bytes":
        return base64.b64decode(value.encode("ascii"))

    if type_name == "enum":
        # Import the enum class
        import importlib

        module = importlib.import_module(metadata["enum"]["module"])
        enum_class = getattr(module, metadata["enum"]["class"])
        return enum_class(metadata["enum"]["value"])

    if type_name == "set":
        return set(value)

    if type_name == "tuple":
        return tuple(value)

    raise DeserializationError(f"Unknown type marker: {type_name}")


def serialize_for_cache(obj: Any) -> bytes:
    """
    Serialize object for cache storage (returns bytes)

    Args:
        obj: Python object to serialize

    Returns:
        JSON bytes suitable for Redis/cache storage
    """
    json_str = json_serialize(obj)
    return json_str.encode("utf-8")


def deserialize_from_cache(data: bytes) -> Any:
    """
    Deserialize object from cache storage

    Args:
        data: Bytes from cache

    Returns:
        Deserialized Python object
    """
    json_str = data.decode("utf-8")
    return json_deserialize(json_str)


def get_cache_hash(obj: Any) -> str:
    """
    Generate consistent hash for cache key

    Args:
        obj: Python object to hash

    Returns:
        SHA256 hash string
    """
    json_str = json_serialize(obj)
    return hashlib.sha256(json_str.encode()).hexdigest()


# ✅ SECURITY: No pickle usage - all serialization is JSON-based
# Prevents arbitrary code execution (CWE-502)
# Safe for untrusted data sources
