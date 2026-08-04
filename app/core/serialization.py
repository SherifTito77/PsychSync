"""
Precision-Preserving JSON Serialization Module

This module provides custom JSON encoder/decoder that preserves:
- Datetime objects with timezone information
- Decimal precision (converts to float for JSON compatibility)
- UUID objects
- Set objects (converted to lists)
- Type information for round-trip serialization

Usage:
    from app.core.serialization import json_dumps_precise, json_loads_precise

    # Serialize
    data = {"timestamp": datetime.now(timezone.utc), "amount": Decimal("99.99")}
    json_str = json_dumps_precise(data)

    # Deserialize (types preserved)
    restored = json_loads_precise(json_str)
"""

import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Union
from uuid import UUID

logger = logging.getLogger(__name__)


class PrecisionJSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder that preserves type information.

    Handles:
    - datetime objects (with timezone)
    - Decimal objects (converts to float)
    - UUID objects
    - set objects (converts to list)
    - bytes objects (converts to base64)
    """

    def default(self, obj: Any) -> Any:
        # Handle datetime objects (preserve timezone)
        if isinstance(obj, datetime):
            return {
                "__type__": "datetime",
                "value": obj.isoformat(),
                "timezone": str(obj.tzinfo) if obj.tzinfo else None,
            }

        # Handle Decimal (convert to float for JSON compatibility)
        # Note: This may lose extreme precision, but JSON doesn't support Decimal natively
        elif isinstance(obj, Decimal):
            return {
                "__type__": "decimal",
                "value": str(obj),  # Keep as string to preserve precision
            }

        # Handle UUID
        elif isinstance(obj, UUID):
            return {"__type__": "uuid", "value": str(obj)}

        # Handle set (convert to list for JSON compatibility)
        elif isinstance(obj, set):
            return {"__type__": "set", "value": list(obj)}

        # Handle frozenset
        elif isinstance(obj, frozenset):
            return {"__type__": "frozenset", "value": list(obj)}

        # Handle bytes (convert to base64 string)
        elif isinstance(obj, bytes):
            import base64

            return {"__type__": "bytes", "value": base64.b64encode(obj).decode("ascii")}

        # Fallback to default behavior
        return super().default(obj)


class PrecisionJSONDecoder(json.JSONDecoder):
    """
    Custom JSON decoder that restores type information.

    Reconstructs:
    - datetime objects with timezone
    - Decimal objects
    - UUID objects
    - set/frozenset objects
    - bytes objects
    """

    def __init__(self, *args, **kwargs):
        kwargs["object_hook"] = self._object_hook
        super().__init__(*args, **kwargs)

    def _object_hook(self, dct: dict) -> Any:
        # Check if this is a typed object
        if not isinstance(dct, dict) or "__type__" not in dct:
            return dct

        obj_type = dct["__type__"]
        value = dct["value"]

        try:
            # Restore datetime objects
            if obj_type == "datetime":
                dt = datetime.fromisoformat(value)
                # Restore timezone if present
                if dct.get("timezone"):
                    # Try to restore timezone
                    try:
                        import pytz

                        tz = pytz.timezone(dct["timezone"])
                        dt = tz.localize(dt)
                    except (ImportError, pytz.UnknownTimeZoneError):
                        # If pytz not available or unknown timezone, try zoneinfo
                        try:
                            from zoneinfo import ZoneInfo

                            dt = dt.replace(tzinfo=ZoneInfo(dct["timezone"]))
                        except (ImportError, Exception):
                            logger.warning(
                                f"Could not restore timezone: {dct['timezone']}"
                            )
                return dt

            # Restore Decimal objects
            elif obj_type == "decimal":
                return Decimal(value)

            # Restore UUID objects
            elif obj_type == "uuid":
                return UUID(value)

            # Restore set objects
            elif obj_type == "set":
                return set(value)

            # Restore frozenset objects
            elif obj_type == "frozenset":
                return frozenset(value)

            # Restore bytes objects
            elif obj_type == "bytes":
                import base64

                return base64.b64decode(value)

        except Exception as e:
            logger.error(f"Error decoding {obj_type}: {e}, returning raw value")
            return value

        return dct


def json_dumps_precise(obj: Any, indent: int = None, **kwargs) -> str:
    """
    Serialize object to JSON with precision preservation.

    Args:
        obj: Object to serialize
        indent: JSON indentation (None for compact)
        **kwargs: Additional arguments passed to json.dumps

    Returns:
        JSON string with preserved type information

    Example:
        data = {"dt": datetime.now(timezone.utc), "amount": Decimal("99.99")}
        json_str = json_dumps_precise(data)
    """
    kwargs.setdefault("cls", PrecisionJSONEncoder)
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("indent", indent)
    return json.dumps(obj, **kwargs)


def json_loads_precise(json_str: Union[str, bytes], **kwargs) -> Any:
    """
    Deserialize JSON string with type restoration.

    Args:
        json_str: JSON string to deserialize
        **kwargs: Additional arguments passed to json.loads

    Returns:
        Deserialized object with types restored

    Example:
        data = json_loads_precise(json_str)
        assert isinstance(data['dt'], datetime)
        assert isinstance(data['amount'], Decimal)
    """
    kwargs.setdefault("cls", PrecisionJSONDecoder)
    return json.loads(json_str, **kwargs)


def json_dumps_compact(obj: Any, **kwargs) -> str:
    """
    Serialize to compact JSON (no indentation, no whitespace).

    Useful for caching and storage where space matters.

    Args:
        obj: Object to serialize
        **kwargs: Additional arguments passed to json_dumps_precise

    Returns:
        Compact JSON string
    """
    return json_dumps_precise(obj, indent=None, separators=(",", ":"), **kwargs)


# Convenience functions for common use cases
def serialize_datetime(dt: datetime) -> dict:
    """
    Serialize datetime to ISO format with timezone info.

    Args:
        dt: Datetime object

    Returns:
        Dict with ISO format string and timezone
    """
    return {"iso": dt.isoformat(), "timezone": str(dt.tzinfo) if dt.tzinfo else None}


def deserialize_datetime(data: dict) -> datetime:
    """
    Deserialize ISO format string back to datetime.

    Args:
        data: Dict with 'iso' and optional 'timezone' keys

    Returns:
        Datetime object with timezone restored if present
    """
    dt = datetime.fromisoformat(data["iso"])

    if data.get("timezone"):
        try:
            import pytz

            tz = pytz.timezone(data["timezone"])
            dt = tz.localize(dt)
        except (ImportError, Exception):
            try:
                from zoneinfo import ZoneInfo

                dt = dt.replace(tzinfo=ZoneInfo(data["timezone"]))
            except Exception:
                logger.warning(f"Could not restore timezone: {data['timezone']}")

    return dt
