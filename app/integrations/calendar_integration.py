# app/integrations/calendar_integration.py
"""
Calendar Events Integration
Connects to Google Calendar/Outlook Calendar APIs
Extracts meeting patterns, focus time, and work-life balance indicators
PRIVACY-ONLY: No meeting content stored, only metadata
"""

import logging
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class MeetingType(Enum):
    """Types of meetings based on metadata"""

    ONE_ON_ONE = "one_on_one"
    TEAM_MEETING = "team_meeting"
    ALL_HANDS = "all_hands"
    CLIENT_MEETING = "client_meeting"
    INTERVIEW = "interview"
    TRAINING = "training"
    FOCUS_TIME = "focus_time"
    OTHER = "other"


@dataclass
class CalendarEvent:
    """Calendar event metadata (no content stored)"""

    event_id: str
    title: str  # Meeting title only
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    attendees_count: int
    is_recurring: bool
    is_all_day: bool
    meeting_type: MeetingType

    # Behavioral flags
    is_after_hours: bool
    is_weekend: bool
    is_back_to_back: bool  # Immediately follows another meeting
    gap_minutes_before: int  # Gap before this meeting
    gap_minutes_after: int  # Gap after this meeting

    # Organizer info
    organizer_email: str
    is_organizer: bool  # Whether user is the organizer

    # Metadata
    organization_id: int
    user_id: int
    connection_id: int


class CalendarMetadataExtractor:
    """
    Extract behavioral signals from calendar metadata
    PRIVACY-FOCUSED: Never stores meeting notes or content
    """

    # Work hours definition
    WORK_HOURS_START = 9  # 9 AM
    WORK_HOURS_END = 18  # 6 PM
    WORK_DAYS = [0, 1, 2, 3, 4]  # Mon-Fri

    # Meeting duration thresholds (minutes)
    SHORT_MEETING = 15
    STANDARD_MEETING = 30
    LONG_MEETING = 60
    MARATHON_MEETING = 120

    def __init__(self, organization_domain: str):
        self.organization_domain = organization_domain

    def extract_from_google_event(
        self,
        event_data: Dict[str, Any],
        user_email: str,
        user_id: int,
        connection_id: int,
        organization_id: int,
    ) -> Optional[CalendarEvent]:
        """
        Extract metadata from Google Calendar API event

        Args:
            event_data: Google Calendar event object
            user_email: User's email address
            user_id: User ID
            connection_id: Calendar connection ID
            organization_id: Organization ID

        Returns:
            CalendarEvent object or None (if declined/cancelled)
        """
        try:
            # Skip cancelled events
            if event_data.get("status") == "cancelled":
                return None

            # Skip declined events
            attendees = event_data.get("attendees", [])
            user_attendee = next(
                (a for a in attendees if a.get("email") == user_email), None
            )
            if user_attendee and user_attendee.get("responseStatus") == "declined":
                return None

            # Parse times
            start_data = event_data.get("start", {})
            end_data = event_data.get("end", {})

            if "dateTime" in start_data:
                start_time = datetime.fromisoformat(
                    start_data["dateTime"].replace("Z", "+00:00")
                )
                end_time = datetime.fromisoformat(
                    end_data["dateTime"].replace("Z", "+00:00")
                )
                is_all_day = False
            else:
                # All-day event
                start_date = start_data.get("date", "")
                start_time = datetime.fromisoformat(start_date)
                end_time = start_time + timedelta(days=1)
                is_all_day = True

            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            # Extract attendees
            attendees_count = len(
                [a for a in attendees if a.get("responseStatus") != "declined"]
            )

            # Check if recurring
            is_recurring = (
                "recurrence" in event_data or "recurringEventId" in event_data
            )

            # Determine meeting type
            title = event_data.get("summary", "No Title")
            meeting_type = self._classify_meeting_type(
                title, attendees_count, duration_minutes
            )

            # Organizer info
            organizer = event_data.get("organizer", {})
            organizer_email = organizer.get("email", "")
            is_organizer = organizer_email == user_email

            # Behavioral flags
            is_after_hours = not is_all_day and (
                start_time.hour < self.WORK_HOURS_START
                or start_time.hour >= self.WORK_HOURS_END
            )
            is_weekend = start_time.weekday() >= 5

            return CalendarEvent(
                event_id=event_data["id"],
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                attendees_count=attendees_count,
                is_recurring=is_recurring,
                is_all_day=is_all_day,
                meeting_type=meeting_type,
                is_after_hours=is_after_hours,
                is_weekend=is_weekend,
                is_back_to_back=False,  # Will be calculated in post-processing
                gap_minutes_before=0,  # Will be calculated in post-processing
                gap_minutes_after=0,  # Will be calculated in post-processing
                organizer_email=organizer_email,
                is_organizer=is_organizer,
                organization_id=organization_id,
                user_id=user_id,
                connection_id=connection_id,
            )

        except Exception as e:
            logger.error(f"Error extracting Google Calendar event: {e}")
            return None

    def extract_from_outlook_event(
        self,
        event_data: Dict[str, Any],
        user_email: str,
        user_id: int,
        connection_id: int,
        organization_id: int,
    ) -> Optional[CalendarEvent]:
        """
        Extract metadata from Microsoft Graph API (Outlook) event

        Args:
            event_data: Microsoft Graph event object
            user_email: User's email address
            user_id: User ID
            connection_id: Calendar connection ID
            organization_id: Organization ID

        Returns:
            CalendarEvent object or None (if declined/cancelled)
        """
        try:
            # Skip cancelled events
            if event_data.get("isCancelled", False):
                return None

            # Skip declined events
            attendees = event_data.get("attendees", [])
            user_attendee = next(
                (
                    a
                    for a in attendees
                    if a.get("email", {}).get("address") == user_email
                ),
                None,
            )
            if (
                user_attendee
                and user_attendee.get("status", {}).get("response") == "declined"
            ):
                return None

            # Parse times
            start_time = datetime.fromisoformat(
                event_data["start"]["dateTime"].replace("Z", "+00:00")
            )
            end_time = datetime.fromisoformat(
                event_data["end"]["dateTime"].replace("Z", "+00:00")
            )

            duration_minutes = int((end_time - start_time).total_seconds() / 60)

            # Extract attendees
            attendees_count = len(
                [
                    a
                    for a in attendees
                    if a.get("status", {}).get("response") not in ["declined", "none"]
                ]
            )

            # Check if recurring
            is_recurring = event_data.get("type") in [
                "seriesMaster",
                "occurrence",
                "exception",
            ]

            # Determine meeting type
            title = event_data.get("subject", "No Title")
            meeting_type = self._classify_meeting_type(
                title, attendees_count, duration_minutes
            )

            # Organizer info
            organizer = event_data.get("organizer", {})
            organizer_email = organizer.get("emailAddress", {}).get("address", "")
            is_organizer = organizer_email == user_email

            # Behavioral flags
            is_after_hours = (
                start_time.hour < self.WORK_HOURS_START
                or start_time.hour >= self.WORK_HOURS_END
            )
            is_weekend = start_time.weekday() >= 5

            # Check if all-day (showAs is 'free' and duration > 8 hours)
            is_all_day = event_data.get("isAllDay", False)

            return CalendarEvent(
                event_id=event_data["id"],
                title=title,
                start_time=start_time,
                end_time=end_time,
                duration_minutes=duration_minutes,
                attendees_count=attendees_count,
                is_recurring=is_recurring,
                is_all_day=is_all_day,
                meeting_type=meeting_type,
                is_after_hours=is_after_hours,
                is_weekend=is_weekend,
                is_back_to_back=False,
                gap_minutes_before=0,
                gap_minutes_after=0,
                organizer_email=organizer_email,
                is_organizer=is_organizer,
                organization_id=organization_id,
                user_id=user_id,
                connection_id=connection_id,
            )

        except Exception as e:
            logger.error(f"Error extracting Outlook event: {e}")
            return None

    def calculate_behavioral_signals(
        self, events: List[CalendarEvent], time_window_days: int = 30
    ) -> Dict[str, Any]:
        """
        Calculate behavioral signals from calendar metadata

        Args:
            events: List of calendar events
            time_window_days: Time window for analysis

        Returns:
            Dictionary of behavioral signals
        """
        if not events:
            return {}

        # Calculate back-to-back meetings and gaps
        events = self._calculate_gaps_and_back_to_back(events)

        signals = {
            "total_meeting_hours": 0.0,
            "avg_meeting_hours_per_day": 0.0,
            "meeting_load_percentage": 0.0,  # % of work time in meetings
            "back_to_back_percentage": 0.0,
            "focus_time_hours_per_day": 0.0,
            "after_hours_meetings_count": 0,
            "weekend_meetings_count": 0,
            "avg_meeting_duration_minutes": 0.0,
            "meeting_frequency": len(events) / time_window_days,
            "one_on_one_frequency": 0.0,
            "large_meeting_percentage": 0.0,  # Meetings with 10+ attendees
            "recurring_meeting_percentage": 0.0,
            "meetings_per_day_distribution": [],
            "meeting_spread_score": 0.0,  # 0-1, higher = more balanced
            "meeting_bunching_score": 0.0,  # 0-1, higher = more bunched
            "organizer_vs_attendee_ratio": 0.0,
            "long_meeting_days": 0,  # Days with >6 hours of meetings
            "meeting_marathons": 0,  # Meetings >2 hours
            "fragmentation_score": 0.0,  # 0-1, higher = more fragmented time
        }

        # Calculate various metrics
        total_duration = 0
        back_to_back_count = 0
        after_hours_count = 0
        weekend_count = 0
        large_meetings = 0
        recurring_count = 0
        one_on_ones = 0
        meeting_marathons = 0
        organizer_count = 0

        daily_meetings = {}  # date -> list of events
        daily_meeting_hours = {}  # date -> total meeting hours

        for event in events:
            total_duration += event.duration_minutes

            if event.is_back_to_back:
                back_to_back_count += 1
            if event.is_after_hours:
                after_hours_count += 1
            if event.is_weekend:
                weekend_count += 1
            if event.attendees_count >= 10:
                large_meetings += 1
            if event.is_recurring:
                recurring_count += 1
            if event.meeting_type == MeetingType.ONE_ON_ONE:
                one_on_ones += 1
            if event.is_organizer:
                organizer_count += 1
            if event.duration_minutes > self.MARATHON_MEETING:
                meeting_marathons += 1

            # Group by day
            date = event.start_time.date()
            if date not in daily_meetings:
                daily_meetings[date] = []
                daily_meeting_hours[date] = 0.0
            daily_meetings[date].append(event)
            daily_meeting_hours[date] += event.duration_minutes / 60.0

        # Convert to hours
        signals["total_meeting_hours"] = total_duration / 60.0
        signals["avg_meeting_hours_per_day"] = (
            signals["total_meeting_hours"] / time_window_days
        )
        signals["avg_meeting_duration_minutes"] = (
            total_duration / len(events) if events else 0
        )

        # Percentages
        total = len(events)
        signals["back_to_back_percentage"] = (
            (back_to_back_count / total) * 100 if total > 0 else 0
        )
        signals["large_meeting_percentage"] = (
            (large_meetings / total) * 100 if total > 0 else 0
        )
        signals["recurring_meeting_percentage"] = (
            (recurring_count / total) * 100 if total > 0 else 0
        )
        signals["organizer_vs_attendee_ratio"] = (
            organizer_count / total if total > 0 else 0
        )

        # Meeting frequency
        signals["one_on_one_frequency"] = one_on_ones / time_window_days

        # After-hours and weekend meetings
        signals["after_hours_meetings_count"] = after_hours_count
        signals["weekend_meetings_count"] = weekend_count

        # Meeting load (% of 8-hour workday)
        signals["meeting_load_percentage"] = min(
            (signals["avg_meeting_hours_per_day"] / 8.0) * 100, 100.0
        )

        # Focus time (uninterrupted blocks > 1 hour)
        focus_time = 0.0
        for date_events in daily_meetings.values():
            sorted_events = sorted(date_events, key=lambda e: e.start_time)
            for i, event in enumerate(sorted_events):
                if event.gap_minutes_before >= 60:
                    focus_time += (
                        min(event.gap_minutes_before, 120) / 60.0
                    )  # Max 2 hours gap
        signals["focus_time_hours_per_day"] = (
            focus_time / len(daily_meetings) if daily_meetings else 0
        )

        # Long meeting days (>6 hours)
        signals["long_meeting_days"] = len(
            [hours for hours in daily_meeting_hours.values() if hours > 6]
        )

        # Meeting spread score (how evenly distributed across days)
        if daily_meeting_hours:
            avg_hours = sum(daily_meeting_hours.values()) / len(daily_meeting_hours)
            variance = sum(
                (h - avg_hours) ** 2 for h in daily_meeting_hours.values()
            ) / len(daily_meeting_hours)
            signals["meeting_spread_score"] = 1.0 - min(
                variance / 25.0, 1.0
            )  # Lower variance = higher spread

        # Meeting bunching score (consecutive meetings)
        consecutive_groups = 0
        for date_events in daily_meetings.values():
            sorted_events = sorted(date_events, key=lambda e: e.start_time)
            i = 0
            while i < len(sorted_events):
                if i > 0 and sorted_events[i].is_back_to_back:
                    # Already counted as part of group
                    pass
                else:
                    consecutive_groups += 1
                i += 1
        signals["meeting_bunching_score"] = (
            1.0 - (consecutive_groups / total) if total > 0 else 0
        )

        # Fragmentation score (average gap size)
        total_gaps = sum(e.gap_minutes_before for e in events)
        signals["fragmentation_score"] = (
            min(total_gaps / (total * 30), 1.0) if total > 0 else 0
        )

        signals["meeting_marathons"] = meeting_marathons

        return signals

    def detect_burnout_indicators(self, signals: Dict[str, Any]) -> List[str]:
        """
        Detect burnout risk indicators from calendar behavioral signals

        Args:
            signals: Behavioral signals dictionary

        Returns:
            List of detected burnout indicators
        """
        indicators = []

        # Check for excessive meeting load
        if signals.get("meeting_load_percentage", 0) > 80:
            indicators.append("Excessive meeting load (>80% of workday)")

        # Check for back-to-back overload
        if signals.get("back_to_back_percentage", 0) > 70:
            indicators.append("Severe back-to-back meeting overload (>70%)")

        # Check for lack of focus time
        if signals.get("focus_time_hours_per_day", 0) < 1:
            indicators.append("Insufficient focus time (<1 hour/day)")

        # Check for after-hours meetings
        if signals.get("after_hours_meetings_count", 0) > 10:
            indicators.append("Frequent after-hours meetings (>10 in period)")

        # Check for weekend meetings
        if signals.get("weekend_meetings_count", 0) > 5:
            indicators.append("Regular weekend meeting activity (>5 in period)")

        # Check for meeting marathons
        if signals.get("meeting_marathons", 0) > 5:
            indicators.append("Frequent marathon meetings (>2 hours, >5 in period)")

        # Check for long meeting days
        if signals.get("long_meeting_days", 0) > 10:
            indicators.append("Multiple long meeting days (>6 hours, >10 days)")

        # Check for high fragmentation
        if signals.get("fragmentation_score", 0) > 0.8:
            indicators.append("Highly fragmented schedule (too many short gaps)")

        # Check for low meeting spread (all meetings on certain days)
        if signals.get("meeting_spread_score", 1.0) < 0.3:
            indicators.append("Unbalanced meeting schedule (bunched on few days)")

        return indicators

    def _classify_meeting_type(
        self, title: str, attendees_count: int, duration_minutes: int
    ) -> MeetingType:
        """Classify meeting type based on metadata"""
        title_lower = title.lower()

        # 1:1 meetings
        if any(
            keyword in title_lower
            for keyword in ["1:1", "1-on-1", "one on one", "check-in"]
        ):
            return MeetingType.ONE_ON_ONE

        # All hands
        if any(
            keyword in title_lower
            for keyword in ["all hands", "all-hands", "town hall", "company meeting"]
        ):
            return MeetingType.ALL_HANDS

        # Training
        if any(
            keyword in title_lower
            for keyword in ["training", "workshop", "learning", "course"]
        ):
            return MeetingType.TRAINING

        # Interview
        if any(
            keyword in title_lower
            for keyword in ["interview", "candidate", "screening"]
        ):
            return MeetingType.INTERVIEW

        # Focus time (blocker meetings)
        if any(
            keyword in title_lower
            for keyword in ["focus time", "deep work", "do not disturb", "block"]
        ):
            return MeetingType.FOCUS_TIME

        # Client meetings (external)
        if any(
            keyword in title_lower
            for keyword in ["client", "customer", "external", "vendor"]
        ):
            return MeetingType.CLIENT_MEETING

        # Team meetings
        if any(
            keyword in title_lower
            for keyword in ["team standup", "daily", "sprint", "retro"]
        ):
            return MeetingType.TEAM_MEETING

        # Large meetings
        if attendees_count > 10:
            return MeetingType.ALL_HANDS

        return MeetingType.OTHER

    def _calculate_gaps_and_back_to_back(
        self, events: List[CalendarEvent]
    ) -> List[CalendarEvent]:
        """Calculate gaps between meetings and back-to-back flags"""
        # Sort by start time
        sorted_events = sorted(events, key=lambda e: e.start_time)

        for i, event in enumerate(sorted_events):
            # Gap before this meeting
            if i > 0:
                prev_event = sorted_events[i - 1]
                gap_minutes = int(
                    (event.start_time - prev_event.end_time).total_seconds() / 60
                )
                event.gap_minutes_before = gap_minutes
                event.is_back_to_back = (
                    gap_minutes < 10
                )  # Less than 10 minutes = back-to-back
            else:
                event.gap_minutes_before = 0
                event.is_back_to_back = False

            # Gap after this meeting
            if i < len(sorted_events) - 1:
                next_event = sorted_events[i + 1]
                gap_minutes = int(
                    (next_event.start_time - event.end_time).total_seconds() / 60
                )
                event.gap_minutes_after = gap_minutes
            else:
                event.gap_minutes_after = 0

        return sorted_events


class GoogleCalendarAPIIntegration:
    """Google Calendar API integration"""

    SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://www.googleapis.com/calendar/v3/calendars/primary"

    async def fetch_events(
        self, days: int = 30, max_results: int = 2500
    ) -> List[Dict[str, Any]]:
        """Fetch calendar events from Google Calendar

        Uses resilient HTTP client with automatic retries, timeouts, and circuit breaker.
        """
        from datetime import datetime, timedelta

        from app.core.resilient_client import resilient_http_client

        time_min = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"
        time_max = datetime.utcnow().isoformat() + "Z"

        # Resilient client provides: 30s timeout, 3 retries with exponential backoff,
        # circuit breaker to prevent cascading failures, connection pooling
        response = await resilient_http_client.get(
            f"{self.base_url}/events",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={
                "timeMin": time_min,
                "timeMax": time_max,
                "maxResults": max_results,
                "singleEvents": "true",
                "orderBy": "startTime",
            },
        )
        response.raise_for_status()

        data = response.json()
        return data.get("items", [])


class OutlookCalendarAPIIntegration:
    """Microsoft Graph API integration for Outlook Calendar"""

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.base_url = "https://graph.microsoft.com/v1.0/me"

    async def fetch_events(
        self, days: int = 30, max_results: int = 500
    ) -> List[Dict[str, Any]]:
        """Fetch calendar events from Outlook

        Uses resilient HTTP client with automatic retries, timeouts, and circuit breaker.
        """
        from datetime import datetime, timedelta

        from app.core.resilient_client import resilient_http_client

        start_date = (datetime.utcnow() - timedelta(days=days)).strftime(
            "%Y-%m-%dT%H:%M:%S"
        )
        end_date = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

        # Resilient client provides: 30s timeout, 3 retries with exponential backoff,
        # circuit breaker to prevent cascading failures, connection pooling
        response = await resilient_http_client.get(
            f"{self.base_url}/calendarView",
            headers={"Authorization": f"Bearer {self.access_token}"},
            params={
                "startDateTime": start_date,
                "endDateTime": end_date,
                "$top": max_results,
            },
        )
        response.raise_for_status()

        data = response.json()
        return data.get("value", [])


# Export
__all__ = [
    "CalendarMetadataExtractor",
    "CalendarEvent",
    "MeetingType",
    "GoogleCalendarAPIIntegration",
    "OutlookCalendarAPIIntegration",
]
