"""Test timestamp and timezone handling in unified analytics

This test suite validates:
- Timezone-aware timestamp storage
- UTC normalization
- DST transition handling
- Timezone validation in API endpoint

"""

from datetime import datetime, timedelta, timezone

import pytest

try:
    from freezegun import freeze_time
except ImportError:
    pytest.skip(
        "freezegun not installed - pip install freezegun to run these tests",
        allow_module_level=True,
    )

from app.api.v1.endpoints.unified_analytics import UnifiedEvent
from app.db.models.analytics import UnifiedAnalyticsEvent


class TestTimezoneValidation:
    """Test Pydantic timezone validation in UnifiedEvent model"""

    def test_accepts_utc_timestamp(self):
        """Test that UTC timestamps are accepted"""
        utc_time = datetime(2026, 1, 21, 10, 30, 0, tzinfo=timezone.utc)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=utc_time,
            session_id="test_session",
            user_id="user_123",
        )

        assert event.timestamp == utc_time
        assert event.timestamp.tzinfo == timezone.utc

    def test_normalizes_naive_timestamp_to_utc(self):
        """Test that naive timestamps are converted to UTC"""
        # Naive datetime (no timezone)
        naive_time = datetime(2026, 1, 21, 10, 30, 0)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=naive_time,
            session_id="test_session",
            user_id="user_123",
        )

        # Should be converted to UTC
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.replace(tzinfo=None) == naive_time

    def test_converts_non_utc_to_utc(self):
        """Test that non-UTC timestamps are converted to UTC"""
        # Eastern Time (UTC-5)
        eastern_tz = timezone(timedelta(hours=-5))
        eastern_time = datetime(2026, 1, 21, 10, 30, 0, tzinfo=eastern_tz)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=eastern_time,
            session_id="test_session",
            user_id="user_123",
        )

        # Should be converted to UTC (10:30 AM EST = 3:30 PM UTC)
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 15  # 3:30 PM UTC
        assert event.timestamp.minute == 30

    def test_utc_plus_five_converted(self):
        """Test conversion from UTC+5 to UTC"""
        # UTC+5 timezone
        plus_five_tz = timezone(timedelta(hours=5))
        local_time = datetime(2026, 1, 21, 15, 30, 0, tzinfo=plus_five_tz)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=local_time,
            session_id="test_session",
            user_id="user_123",
        )

        # Should be converted to UTC (3:30 PM UTC+5 = 10:30 AM UTC)
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 10  # 10:30 AM UTC
        assert event.timestamp.minute == 30


class TestTimezoneStorage:
    """Test timezone-aware storage in database"""

    def test_model_accepts_timezone_aware_datetime(self):
        """Test that database model accepts timezone-aware datetimes"""
        utc_time = datetime(2026, 1, 21, 10, 30, 0, tzinfo=timezone.utc)

        # Create model instance
        event = UnifiedAnalyticsEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=utc_time,
            session_id="test_session",
            user_id="user_123",
        )

        assert event.timestamp == utc_time
        assert event.timestamp.tzinfo == timezone.utc

    def test_model_preserves_timezone_info(self):
        """Test that timezone information is preserved"""
        utc_time = datetime(2026, 1, 21, 10, 30, 0, tzinfo=timezone.utc)

        event = UnifiedAnalyticsEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=utc_time,
            session_id="test_session",
        )

        # Timezone info should be preserved
        assert event.timestamp.tzinfo is not None
        assert event.timestamp.tzinfo == timezone.utc


class TestDSTHandling:
    """Test Daylight Saving Time transition handling"""

    def test_spring_forward_transition(self):
        """Test timestamps during spring DST transition (clocks jump forward)"""
        # In US/Eastern, March 14, 2026 at 2:00 AM clocks jump to 3:00 AM
        # This time doesn't exist in local time, but exists in UTC
        dst_time = datetime(2026, 3, 14, 7, 0, 0, tzinfo=timezone.utc)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=dst_time,
            session_id="test_session",
        )

        # Should handle DST transition correctly
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 7

    def test_fall_back_transition(self):
        """Test timestamps during fall DST transition (clocks fall back)"""
        # In US/Eastern, November 1, 2026 at 2:00 AM clocks repeat to 1:00 AM
        # This creates ambiguity, but UTC is unambiguous
        dst_time = datetime(2026, 11, 1, 5, 0, 0, tzinfo=timezone.utc)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=dst_time,
            session_id="test_session",
        )

        # Should handle DST transition correctly
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 5


class TestISO8601Parsing:
    """Test ISO 8601 format parsing from frontend"""

    def test_parse_iso8601_with_z_suffix(self):
        """Test parsing ISO 8601 timestamp with Z suffix (UTC)"""
        iso_timestamp = "2026-01-21T10:30:00.000Z"

        # Frontend sends ISO 8601 format
        parsed_time = datetime.fromisoformat(iso_timestamp.replace("Z", "+00:00"))

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=parsed_time,
            session_id="test_session",
        )

        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 10

    def test_parse_iso8601_with_timezone_offset(self):
        """Test parsing ISO 8601 timestamp with timezone offset"""
        # Timestamp with +05:00 offset
        iso_timestamp = "2026-01-21T15:30:00.000+05:00"

        parsed_time = datetime.fromisoformat(iso_timestamp)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=parsed_time,
            session_id="test_session",
        )

        # Should be converted to UTC
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 10  # 15:30 UTC+5 = 10:30 UTC

    def test_parse_iso8601_with_negative_offset(self):
        """Test parsing ISO 8601 timestamp with negative timezone offset"""
        # Timestamp with -05:00 offset (Eastern Time)
        iso_timestamp = "2026-01-21T10:30:00.000-05:00"

        parsed_time = datetime.fromisoformat(iso_timestamp)

        event = UnifiedEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=parsed_time,
            session_id="test_session",
        )

        # Should be converted to UTC
        assert event.timestamp.tzinfo == timezone.utc
        assert event.timestamp.hour == 15  # 10:30 EST = 15:30 UTC


class TestTimestampOrdering:
    """Test timestamp ordering and comparisons"""

    def test_timestamp_comparison_works(self):
        """Test that timezone-aware timestamps can be compared"""
        time1 = datetime(2026, 1, 21, 10, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2026, 1, 21, 11, 0, 0, tzinfo=timezone.utc)

        assert time2 > time1
        assert time1 < time2

    def test_timestamp_ordering_with_different_zones(self):
        """Test timestamp ordering with different timezones"""
        # Same moment in different timezones
        utc_time = datetime(2026, 1, 21, 15, 0, 0, tzinfo=timezone.utc)
        eastern_time = datetime(
            2026, 1, 21, 10, 0, 0, tzinfo=timezone(timedelta(hours=-5))
        )

        # Should be equal when converted to same timezone
        assert utc_time == eastern_time.astimezone(timezone.utc)


@pytest.mark.integration
class TestDatabaseTimestampStorage:
    """Integration tests for database timestamp storage"""

    def test_utc_timestamp_preserved_in_db(self, db_session):
        """Test that UTC timestamps are preserved correctly in database"""
        original_time = datetime(2026, 1, 21, 10, 30, 0, tzinfo=timezone.utc)

        event = UnifiedAnalyticsEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=original_time,
            session_id="test_session",
            user_id="user_123",
        )

        db_session.add(event)
        db_session.commit()

        # Retrieve from database
        stored_event = db_session.query(UnifiedAnalyticsEvent).first()

        # Should be exactly the same (no timezone conversion)
        assert stored_event.timestamp == original_time
        assert stored_event.timestamp.tzinfo == timezone.utc
        assert stored_event.timestamp.hour == 10

    def test_timezone_aware_column_type(self, db_session):
        """Test that database column is timezone-aware"""
        from sqlalchemy import text

        # Check column type
        result = db_session.execute(
            text(
                """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'unified_analytics_events'
            AND column_name = 'timestamp'
        """
            )
        ).fetchone()

        # Should be "timestamp with time zone"
        assert result is not None
        assert "with time zone" in result[0].lower()

    def test_created_at_is_timezone_aware(self, db_session):
        """Test that created_at column is timezone-aware"""
        from sqlalchemy import text

        # Check column type
        result = db_session.execute(
            text(
                """
            SELECT data_type
            FROM information_schema.columns
            WHERE table_name = 'unified_analytics_events'
            AND column_name = 'created_at'
        """
            )
        ).fetchone()

        # Should be "timestamp with time zone"
        assert result is not None
        assert "with time zone" in result[0].lower()


@pytest.mark.api
class TestAPITimezoneHandling:
    """API endpoint timezone handling tests"""

    def test_api_accepts_utc_timestamp(self, client):
        """Test that API endpoint accepts UTC timestamps"""
        event = {
            "event_name": "user_button_clicked",
            "event_type": "track",
            "timestamp": "2026-01-21T10:30:00.000Z",
            "session_id": "test_session",
            "user_id": "user_123",
        }

        response = client.post("/api/v1/analytics/track", json={"events": [event]})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["events_processed"] == 1

    def test_api_handles_non_utc_timestamp(self, client):
        """Test that API endpoint handles non-UTC timestamps"""
        event = {
            "event_name": "user_button_clicked",
            "event_type": "track",
            "timestamp": "2026-01-21T10:30:00.000+05:00",  # UTC+5
            "session_id": "test_session",
        }

        response = client.post("/api/v1/analytics/track", json={"events": [event]})

        # Should accept and convert to UTC
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_api_query_with_timestamp_range(self, client, db_session):
        """Test querying events with timestamp range"""
        from app.db.models.analytics import UnifiedAnalyticsEvent

        # Create test events
        time1 = datetime(2026, 1, 21, 10, 0, 0, tzinfo=timezone.utc)
        time2 = datetime(2026, 1, 21, 11, 0, 0, tzinfo=timezone.utc)

        event1 = UnifiedAnalyticsEvent(
            event_name="user_button_clicked",
            event_type="track",
            timestamp=time1,
            session_id="test_session",
        )

        event2 = UnifiedAnalyticsEvent(
            event_name="user_link_clicked",
            event_type="track",
            timestamp=time2,
            session_id="test_session",
        )

        db_session.add(event1)
        db_session.add(event2)
        db_session.commit()

        # Query with timestamp range
        response = client.get(
            "/api/v1/analytics/events",
            params={
                "start_date": "2026-01-21T09:00:00Z",
                "end_date": "2026-01-21T10:30:00Z",
            },
        )

        assert response.status_code == 200
        data = response.json()
        # Should only return first event
        assert len(data["events"]) == 1
        assert data["events"][0]["event_name"] == "user_button_clicked"
