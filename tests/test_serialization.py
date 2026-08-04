"""
Comprehensive Serialization Tests

Tests for precision-preserving JSON serialization/deserialization.
This ensures data integrity through cache round-trips.

Coverage:
- Datetime objects (with/without timezone)
- Decimal precision
- UUID handling
- Set/frozenset conversion
- Complex nested structures
- Type round-trip preservation
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

import pytest

from app.core.serialization import (
    deserialize_datetime,
    json_dumps_compact,
    json_dumps_precise,
    json_loads_precise,
    serialize_datetime,
)


class TestDatetimeSerialization:
    """Test datetime serialization preserves timezone information"""

    def test_datetime_with_timezone(self):
        """Test timezone-aware datetime round-trip"""
        # Create timezone-aware datetime
        original_dt = datetime(2024, 1, 20, 15, 30, 45, 123456, tzinfo=timezone.utc)

        # Serialize and deserialize
        data = {"timestamp": original_dt}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        # Assert datetime object restored
        assert isinstance(restored["timestamp"], datetime)
        assert restored["timestamp"] == original_dt

    def test_datetime_without_timezone(self):
        """Test naive datetime round-trip"""
        original_dt = datetime(2024, 1, 20, 15, 30, 45, 123456)

        data = {"timestamp": original_dt}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["timestamp"], datetime)
        # Note: naive datetime preserved as-is

    def test_datetime_precision(self):
        """Test microsecond precision preserved"""
        original_dt = datetime(2024, 1, 20, 15, 30, 45, 999999, tzinfo=timezone.utc)

        json_str = json_dumps_precise({"dt": original_dt})
        restored = json_loads_precise(json_str)

        # Check microseconds preserved
        assert restored["dt"].microsecond == 999999

    def test_multiple_datetimes(self):
        """Test multiple datetime objects in same structure"""
        data = {
            "created_at": datetime(2024, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc),
            "deleted_at": None,
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["created_at"], datetime)
        assert isinstance(restored["updated_at"], datetime)
        assert restored["deleted_at"] is None


class TestDecimalSerialization:
    """Test Decimal precision preservation"""

    def test_decimal_basic(self):
        """Test basic Decimal round-trip"""
        original = Decimal("123.456789")

        data = {"amount": original}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        # Decimal preserved as string, then restored
        assert isinstance(restored["amount"], Decimal)
        assert str(restored["amount"]) == "123.456789"

    def test_decimal_scientific_notation(self):
        """Test very large and very small decimals"""
        large = Decimal("1.23E+10")
        small = Decimal("1.23E-10")

        data = {"large": large, "small": small}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["large"] == large
        assert restored["small"] == small

    def test_decimal_high_precision(self):
        """Test Decimal with many decimal places"""
        original = Decimal("99.999999999999999999")

        data = {"value": original}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["value"] == original


class TestUUIDSerialization:
    """Test UUID handling"""

    def test_uuid_round_trip(self):
        """Test UUID object round-trip"""
        original_uuid = uuid4()

        data = {"id": original_uuid}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["id"], UUID)
        assert restored["id"] == original_uuid

    def test_multiple_uuids(self):
        """Test multiple UUID objects"""
        uuid1 = uuid4()
        uuid2 = uuid4()

        data = {"primary": uuid1, "secondary": uuid2}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["primary"] == uuid1
        assert restored["secondary"] == uuid2


class TestSetSerialization:
    """Test set/frozenset conversion"""

    def test_set_round_trip(self):
        """Test set converted to list and back"""
        original_set = {1, 2, 3, 4, 5}

        data = {"numbers": original_set}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        # Set should be restored
        assert isinstance(restored["numbers"], set)
        assert restored["numbers"] == original_set

    def test_frozenset_round_trip(self):
        """Test frozenset round-trip"""
        original_frozenset = frozenset([1, 2, 3])

        data = {"immutable_set": original_frozenset}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["immutable_set"], frozenset)
        assert restored["immutable_set"] == original_frozenset

    def test_set_of_strings(self):
        """Test set containing strings"""
        original_set = {"apple", "banana", "cherry"}

        data = {"fruits": original_set}
        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["fruits"] == original_set


class TestComplexStructures:
    """Test complex nested data structures"""

    def test_nested_dict(self):
        """Test nested dictionary with mixed types"""
        data = {
            "user": {
                "id": uuid4(),
                "created_at": datetime.now(timezone.utc),
                "balance": Decimal("100.50"),
                "tags": {"tag1", "tag2"},
            }
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["user"]["id"], UUID)
        assert isinstance(restored["user"]["created_at"], datetime)
        assert isinstance(restored["user"]["balance"], Decimal)
        assert isinstance(restored["user"]["tags"], set)

    def test_list_of_complex_objects(self):
        """Test list containing complex objects"""
        data = {
            "events": [
                {
                    "id": uuid4(),
                    "timestamp": datetime(2024, 1, i, tzinfo=timezone.utc),
                    "value": Decimal(f"{i}.99"),
                }
                for i in range(1, 4)
            ]
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert len(restored["events"]) == 3
        for event in restored["events"]:
            assert isinstance(event["id"], UUID)
            assert isinstance(event["timestamp"], datetime)
            assert isinstance(event["value"], Decimal)

    def test_deeply_nested(self):
        """Test deeply nested structure"""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "datetime": datetime.now(timezone.utc),
                        "decimal": Decimal("3.14159"),
                        "uuid": uuid4(),
                    }
                }
            }
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert isinstance(restored["level1"]["level2"]["level3"]["datetime"], datetime)
        assert isinstance(restored["level1"]["level2"]["level3"]["decimal"], Decimal)
        assert isinstance(restored["level1"]["level2"]["level3"]["uuid"], UUID)


class TestCompactSerialization:
    """Test compact JSON serialization"""

    def test_compact_no_whitespace(self):
        """Test compact serialization has no whitespace"""
        data = {"key": "value", "number": 123}

        compact = json_dumps_compact(data)
        normal = json_dumps_precise(data)

        # Compact should be shorter
        assert len(compact) < len(normal)
        # Compact should not have newlines
        assert "\n" not in compact

    def test_compact_preserves_types(self):
        """Test compact serialization still preserves types"""
        data = {
            "dt": datetime.now(timezone.utc),
            "decimal": Decimal("99.99"),
        }

        compact = json_dumps_compact(data)
        restored = json_loads_precise(compact)

        assert isinstance(restored["dt"], datetime)
        assert isinstance(restored["decimal"], Decimal)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_none_values(self):
        """Test None value handling"""
        data = {"null_value": None, "normal_value": 123}

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["null_value"] is None
        assert restored["normal_value"] == 123

    def test_empty_structures(self):
        """Test empty dicts, lists, sets"""
        data = {
            "empty_dict": {},
            "empty_list": [],
            "empty_set": set(),
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["empty_dict"] == {}
        assert restored["empty_list"] == []
        assert restored["empty_set"] == set()

    def test_unicode(self):
        """Test Unicode string handling"""
        data = {
            "emoji": "😀🎉",
            "chinese": "中文",
            "arabic": "العربية",
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["emoji"] == "😀🎉"
        assert restored["chinese"] == "中文"
        assert restored["arabic"] == "العربية"

    def test_special_characters(self):
        """Test special characters in strings"""
        data = {
            "newline": "line1\nline2",
            "tab": "col1\tcol2",
            "quote": 'He said "hello"',
        }

        json_str = json_dumps_precise(data)
        restored = json_loads_precise(json_str)

        assert restored["newline"] == "line1\nline2"
        assert restored["tab"] == "col1\tcol2"
        assert restored["quote"] == 'He said "hello"'


class TestDatetimeHelperFunctions:
    """Test datetime helper serialization functions"""

    def test_serialize_datetime_helper(self):
        """Test serialize_datetime helper"""
        dt = datetime(2024, 1, 20, 15, 30, 45, tzinfo=timezone.utc)

        result = serialize_datetime(dt)

        assert "iso" in result
        assert "timezone" in result
        assert result["iso"] == dt.isoformat()
        assert result["timezone"] == "UTC"

    def test_deserialize_datetime_helper(self):
        """Test deserialize_datetime helper"""
        data = {"iso": "2024-01-20T15:30:45+00:00", "timezone": "UTC"}

        dt = deserialize_datetime(data)

        assert isinstance(dt, datetime)
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 20


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_api_response_serialization(self):
        """Test typical API response with various types"""
        response = {
            "id": uuid4(),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "score": Decimal("97.5"),
            "metadata": {
                "tags": {"important", "reviewed"},
                "count": 42,
            },
        }

        json_str = json_dumps_precise(response)
        restored = json_loads_precise(json_str)

        assert restored["id"] == response["id"]
        assert isinstance(restored["created_at"], datetime)
        assert restored["score"] == Decimal("97.5")

    def test_cache_round_trip(self):
        """Test typical cache data round-trip"""
        cache_data = {
            "user_id": uuid4(),
            "session_start": datetime.now(timezone.utc),
            "last_activity": datetime.now(timezone.utc),
            "preferences": {
                "theme": "dark",
                "notifications": True,
            },
            "cart_total": Decimal("123.45"),
        }

        # Simulate cache round-trip
        serialized = json_dumps_precise(cache_data)
        deserialized = json_loads_precise(serialized)

        # All types preserved
        assert isinstance(deserialized["user_id"], UUID)
        assert isinstance(deserialized["session_start"], datetime)
        assert isinstance(deserialized["last_activity"], datetime)
        assert isinstance(deserialized["cart_total"], Decimal)
        assert deserialized["preferences"]["theme"] == "dark"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
