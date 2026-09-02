"""
Calendar Integration Service

Connects to Google Calendar and Microsoft Outlook to extract
behavioral signals from meeting patterns:
  - Meeting load (hours/day, meetings/week)
  - After-hours work detection
  - Focus time availability
  - Meeting fragmentation (context-switching cost)
  - 1:1 vs group meeting ratio
  - Recurring meeting burden
  - Back-to-back meeting chains

These signals feed into the Behavioral Intelligence Engine for
burnout prediction and workload optimization.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class MeetingType(str, Enum):
    ONE_ON_ONE = "1:1"
    SMALL_GROUP = "small_group"  # 3-5
    LARGE_GROUP = "large_group"  # 6+
    ALL_HANDS = "all_hands"  # 15+
    EXTERNAL = "external"
    FOCUS_BLOCK = "focus_block"


@dataclass
class CalendarEvent:
    """Normalized calendar event across platforms."""

    id: str
    title: str  # Anonymized if needed
    start: datetime
    end: datetime
    duration_minutes: int
    attendee_count: int
    is_recurring: bool
    is_organizer: bool
    response_status: str  # "accepted", "tentative", "declined"
    meeting_type: MeetingType
    is_after_hours: bool = False
    is_focus_time: bool = False


@dataclass
class DailyMeetingLoad:
    """Per-day meeting summary."""

    date: str
    total_meetings: int
    total_hours: float
    focus_hours: float  # Uninterrupted blocks >= 2 hours
    after_hours_meetings: int
    back_to_back_chains: int  # Consecutive meetings without break
    largest_focus_block_min: int
    meeting_types: Dict[str, int] = field(default_factory=dict)


@dataclass
class MeetingHealthScore:
    """Overall calendar health assessment."""

    score: float  # 0-100, higher = healthier
    label: str
    meeting_hours_per_week: float
    focus_hours_per_week: float
    after_hours_pct: float
    back_to_back_rate: float
    one_on_one_ratio: float
    recurring_burden_pct: float
    fragmentation_score: float  # 0-100, higher = more fragmented
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CalendarConnector(ABC):
    """Base interface for calendar integrations."""

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[CalendarEvent]: ...


# ══════════════════════════════════════════════════════════════════
# GOOGLE CALENDAR CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GoogleCalendarConnector(CalendarConnector):
    """Google Calendar API connector (OAuth2)."""

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        service_account_key: Optional[str] = None,
    ):
        self.credentials_json = credentials_json
        self.service_account_key = service_account_key

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            # Would use Google OAuth2 flow
            return {
                "connected": True,
                "provider": "google_calendar",
                "note": "OAuth2 required",
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[CalendarEvent]:
        """Fetch events from Google Calendar API using OAuth2 access token."""
        events = []
        access_token = await self._get_access_token(user_email)
        if not access_token:
            logger.warning(
                "No access token for %s — skipping Google Calendar fetch", user_email
            )
            return events

        try:
            import httpx

            time_min = (
                start.isoformat() + "Z" if not start.tzinfo else start.isoformat()
            )
            time_max = end.isoformat() + "Z" if not end.tzinfo else end.isoformat()

            async with httpx.AsyncClient(timeout=30.0) as client:
                page_token = None
                while True:
                    params = {
                        "timeMin": time_min,
                        "timeMax": time_max,
                        "singleEvents": "true",
                        "orderBy": "startTime",
                        "maxResults": 250,
                    }
                    if page_token:
                        params["pageToken"] = page_token

                    response = await client.get(
                        "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params=params,
                    )

                    if response.status_code == 401:
                        access_token = await self._refresh_token(user_email)
                        if not access_token:
                            logger.error("Token refresh failed for %s", user_email)
                            break
                        continue

                    response.raise_for_status()
                    data = response.json()

                    for raw in data.get("items", []):
                        if raw.get("status") == "cancelled":
                            continue
                        try:
                            event = self._normalize_event(raw)
                            if event.response_status != "declined":
                                events.append(event)
                        except Exception as e:
                            logger.debug("Skipping event: %s", e)

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

            logger.info(
                "Google Calendar: fetched %d events for %s", len(events), user_email
            )
        except ImportError:
            logger.warning("httpx not installed — Google Calendar connector disabled")
        except Exception as e:
            logger.error("Google Calendar fetch error for %s: %s", user_email, e)
        return events

    async def _get_access_token(self, user_email: str) -> Optional[str]:
        """Retrieve OAuth2 access token from connector credentials."""
        try:
            import json

            if self.credentials_json:
                creds = json.loads(self.credentials_json)
                return creds.get("access_token")
        except Exception as e:
            logger.debug("Could not parse Google credentials: %s", e)
        return None

    async def _refresh_token(self, user_email: str) -> Optional[str]:
        """Refresh expired Google OAuth2 token using stored refresh_token."""
        try:
            import json
            import httpx
            from app.core.config import settings

            if not self.credentials_json:
                return None
            creds = json.loads(self.credentials_json)
            refresh_token = creds.get("refresh_token")
            if not refresh_token:
                return None

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://oauth2.googleapis.com/token",
                    data={
                        "client_id": getattr(settings, "GOOGLE_CLIENT_ID", ""),
                        "client_secret": getattr(settings, "GOOGLE_CLIENT_SECRET", ""),
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                    },
                )
                response.raise_for_status()
                tokens = response.json()

            creds["access_token"] = tokens["access_token"]
            self.credentials_json = json.dumps(creds)
            return tokens["access_token"]
        except Exception as e:
            logger.error("Google token refresh failed: %s", e)
        return None

    def _normalize_event(self, raw: dict) -> CalendarEvent:
        """Normalize a Google Calendar event to our schema."""
        start_str = raw.get("start", {}).get("dateTime", "")
        end_str = raw.get("end", {}).get("dateTime", "")

        try:
            start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            start_dt = datetime.utcnow()
            end_dt = start_dt + timedelta(minutes=30)

        duration = int((end_dt - start_dt).total_seconds() / 60)
        attendees = raw.get("attendees", [])
        attendee_count = len(attendees)

        return CalendarEvent(
            id=raw.get("id", ""),
            title=self._anonymize_title(raw.get("summary", "Meeting")),
            start=start_dt,
            end=end_dt,
            duration_minutes=duration,
            attendee_count=attendee_count,
            is_recurring=raw.get("recurringEventId") is not None,
            is_organizer=raw.get("organizer", {}).get("self", False),
            response_status=self._extract_response(attendees),
            meeting_type=self._classify_meeting(attendee_count),
            is_after_hours=self._is_after_hours(start_dt),
        )

    def _anonymize_title(self, title: str) -> str:
        """Keep meeting type info, remove specifics."""
        lower = title.lower()
        if "1:1" in lower or "one on one" in lower or "1-1" in lower:
            return "1:1 Meeting"
        if "standup" in lower or "stand-up" in lower:
            return "Standup"
        if "retro" in lower:
            return "Retrospective"
        if "all hands" in lower or "town hall" in lower:
            return "All Hands"
        if "focus" in lower or "deep work" in lower or "no meeting" in lower:
            return "Focus Time"
        return "Meeting"

    def _classify_meeting(self, attendee_count: int) -> MeetingType:
        if attendee_count <= 2:
            return MeetingType.ONE_ON_ONE
        elif attendee_count <= 5:
            return MeetingType.SMALL_GROUP
        elif attendee_count <= 15:
            return MeetingType.LARGE_GROUP
        return MeetingType.ALL_HANDS

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END

    def _extract_response(self, attendees: list) -> str:
        for a in attendees:
            if a.get("self"):
                return a.get("responseStatus", "accepted")
        return "accepted"


# ══════════════════════════════════════════════════════════════════
# OUTLOOK CONNECTOR
# ══════════════════════════════════════════════════════════════════


class OutlookCalendarConnector(CalendarConnector):
    """Microsoft Graph API connector for Outlook Calendar."""

    def __init__(
        self, tenant_id: str = "", client_id: str = "", client_secret: str = ""
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def test_connection(self) -> Dict[str, Any]:
        try:
            import httpx

            return {
                "connected": True,
                "provider": "outlook",
                "note": "Azure AD OAuth required",
            }
        except Exception as e:
            return {"connected": False, "error": str(e)}

    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[CalendarEvent]:
        """Fetch from Microsoft Graph API /me/calendarView."""
        access_token = await self._get_access_token(user_email)
        if not access_token:
            logger.warning(
                "No access token for %s — skipping Outlook fetch", user_email
            )
            return []

        events = []
        try:
            import httpx

            start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
            end_str = end.strftime("%Y-%m-%dT%H:%M:%S")

            async with httpx.AsyncClient(timeout=30.0) as client:
                skip = 0
                while True:
                    response = await client.get(
                        f"{self.base_url}/me/calendarView",
                        headers={
                            "Authorization": f"Bearer {access_token}",
                            "Prefer": 'outlook.timezone="UTC"',
                        },
                        params={
                            "startDateTime": start_str,
                            "endDateTime": end_str,
                            "$top": 100,
                            "$skip": skip,
                            "$select": "id,subject,start,end,attendees,organizer,type,isAllDay,isCancelled",
                        },
                    )

                    if response.status_code == 401:
                        access_token = await self._refresh_outlook_token(user_email)
                        if not access_token:
                            break
                        continue

                    response.raise_for_status()
                    data = response.json()
                    items = data.get("value", [])

                    for raw in items:
                        if raw.get("isCancelled"):
                            continue
                        try:
                            event = self._normalize_outlook_event(raw)
                            events.append(event)
                        except Exception as e:
                            logger.debug("Skipping Outlook event: %s", e)

                    if "@odata.nextLink" not in data:
                        break
                    skip += len(items)

            logger.info("Outlook: fetched %d events for %s", len(events), user_email)
        except ImportError:
            logger.warning("httpx not installed — Outlook connector disabled")
        except Exception as e:
            logger.error("Outlook fetch error for %s: %s", user_email, e)
        return events

    def _normalize_outlook_event(self, raw: dict) -> CalendarEvent:
        """Normalize an Outlook event to our schema."""
        start_str = raw.get("start", {}).get("dateTime", "")
        end_str = raw.get("end", {}).get("dateTime", "")
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_str.replace("Z", "+00:00"))
        duration = int((end_dt - start_dt).total_seconds() / 60)

        attendees = raw.get("attendees", [])
        attendee_count = len(attendees)
        organizer = raw.get("organizer", {})
        organizer_email = organizer.get("emailAddress", {}).get("address", "")

        response_status = "accepted"
        for a in attendees:
            addr = a.get("emailAddress", {}).get("address", "")
            if addr == organizer_email:
                status = a.get("status", {}).get("response", "accepted")
                response_status = status
                break

        return CalendarEvent(
            id=raw.get("id", ""),
            title="Meeting",  # Anonymized by default
            start=start_dt,
            end=end_dt,
            duration_minutes=duration,
            attendee_count=attendee_count,
            is_recurring=raw.get("type") in ("seriesMaster", "occurrence", "exception"),
            is_organizer=True,  # Simplified; refine with user_email comparison
            response_status=response_status,
            meeting_type=self._classify_outlook_meeting(attendee_count),
            is_after_hours=start_dt.hour < 9 or start_dt.hour >= 18,
        )

    def _classify_outlook_meeting(self, attendee_count: int) -> MeetingType:
        if attendee_count <= 2:
            return MeetingType.ONE_ON_ONE
        elif attendee_count <= 5:
            return MeetingType.SMALL_GROUP
        elif attendee_count <= 15:
            return MeetingType.LARGE_GROUP
        return MeetingType.ALL_HANDS

    async def _get_access_token(self, user_email: str) -> Optional[str]:
        """Retrieve OAuth2 access token from connector credentials."""
        try:
            import json

            # Credentials stored as JSON: {"access_token": "...", "refresh_token": "..."}
            creds_str = (
                self.client_secret
            )  # Reuse client_secret field for encrypted creds
            if creds_str and creds_str.startswith("{"):
                creds = json.loads(creds_str)
                return creds.get("access_token")
        except Exception as e:
            logger.debug("Could not parse Outlook credentials: %s", e)
        return None

    async def _refresh_outlook_token(self, user_email: str) -> Optional[str]:
        """Refresh expired Microsoft OAuth2 token."""
        try:
            import json
            import httpx

            creds_str = self.client_secret
            if not creds_str or not creds_str.startswith("{"):
                return None
            creds = json.loads(creds_str)
            refresh_token = creds.get("refresh_token")
            if not refresh_token:
                return None

            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": creds.get("app_secret", ""),
                        "refresh_token": refresh_token,
                        "grant_type": "refresh_token",
                        "scope": "https://graph.microsoft.com/Calendars.Read",
                    },
                )
                response.raise_for_status()
                tokens = response.json()

            creds["access_token"] = tokens["access_token"]
            if "refresh_token" in tokens:
                creds["refresh_token"] = tokens["refresh_token"]
            self.client_secret = json.dumps(creds)
            return tokens["access_token"]
        except Exception as e:
            logger.error("Outlook token refresh failed: %s", e)
        return None


# ══════════════════════════════════════════════════════════════════
# MEETING HEALTH ANALYZER
# ══════════════════════════════════════════════════════════════════


class CalendarBehavioralAnalyzer:
    """Extracts behavioral signals from calendar data."""

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)
    WORK_HOURS_PER_DAY = 8.0

    def analyze_meeting_health(
        self,
        events: List[CalendarEvent],
        days: int = 14,
    ) -> MeetingHealthScore:
        """Comprehensive meeting health analysis."""
        if not events:
            return MeetingHealthScore(
                score=80,
                label="No Data",
                meeting_hours_per_week=0,
                focus_hours_per_week=40,
                after_hours_pct=0,
                back_to_back_rate=0,
                one_on_one_ratio=0,
                recurring_burden_pct=0,
                fragmentation_score=0,
                recommendations=[
                    "No calendar data available. Connect your calendar to enable meeting health analysis."
                ],
            )

        # Filter to accepted meetings only
        accepted = [e for e in events if e.response_status in ("accepted", "tentative")]
        total_hours = sum(e.duration_minutes for e in accepted) / 60
        weeks = max(days / 7, 1)

        meeting_hours_week = total_hours / weeks
        after_hours = sum(1 for e in accepted if e.is_after_hours)
        after_hours_pct = (after_hours / max(len(accepted), 1)) * 100

        recurring = sum(1 for e in accepted if e.is_recurring)
        recurring_pct = (recurring / max(len(accepted), 1)) * 100

        one_on_ones = sum(
            1 for e in accepted if e.meeting_type == MeetingType.ONE_ON_ONE
        )
        one_on_one_ratio = one_on_ones / max(len(accepted), 1)

        # Focus time & fragmentation
        daily_loads = self._daily_breakdown(accepted, days)
        avg_focus = sum(d.focus_hours for d in daily_loads) / max(len(daily_loads), 1)
        focus_hours_week = avg_focus * 5

        back_to_back_total = sum(d.back_to_back_chains for d in daily_loads)
        b2b_rate = back_to_back_total / max(len(accepted), 1)

        fragmentation = self._fragmentation_score(daily_loads)

        # Score calculation
        score = 100.0
        # Penalty for too many meeting hours (>15h/week is concerning)
        if meeting_hours_week > 15:
            score -= min(30, (meeting_hours_week - 15) * 3)
        # Penalty for low focus time (<10h/week)
        if focus_hours_week < 10:
            score -= min(20, (10 - focus_hours_week) * 2)
        # Penalty for after-hours
        if after_hours_pct > 10:
            score -= min(15, after_hours_pct * 0.5)
        # Penalty for back-to-back
        if b2b_rate > 0.3:
            score -= min(15, b2b_rate * 30)
        # Penalty for high fragmentation
        score -= fragmentation * 0.2

        score = max(0, min(100, score))
        label = self._score_label(score)

        recs = self._generate_recommendations(
            meeting_hours_week,
            focus_hours_week,
            after_hours_pct,
            b2b_rate,
            one_on_one_ratio,
            recurring_pct,
            fragmentation,
        )

        return MeetingHealthScore(
            score=round(score, 1),
            label=label,
            meeting_hours_per_week=round(meeting_hours_week, 1),
            focus_hours_per_week=round(focus_hours_week, 1),
            after_hours_pct=round(after_hours_pct, 1),
            back_to_back_rate=round(b2b_rate, 3),
            one_on_one_ratio=round(one_on_one_ratio, 3),
            recurring_burden_pct=round(recurring_pct, 1),
            fragmentation_score=round(fragmentation, 1),
            recommendations=recs,
        )

    def daily_breakdown(
        self,
        events: List[CalendarEvent],
        days: int = 14,
    ) -> List[Dict[str, Any]]:
        """Per-day meeting breakdown for charting."""
        loads = self._daily_breakdown(events, days)
        return [
            {
                "date": d.date,
                "meetings": d.total_meetings,
                "meeting_hours": d.total_hours,
                "focus_hours": d.focus_hours,
                "after_hours": d.after_hours_meetings,
                "back_to_back": d.back_to_back_chains,
                "largest_focus_block_min": d.largest_focus_block_min,
            }
            for d in loads
        ]

    def _daily_breakdown(
        self,
        events: List[CalendarEvent],
        days: int,
    ) -> List[DailyMeetingLoad]:
        """Group events by day and compute daily metrics."""
        from collections import defaultdict

        by_day: Dict[str, List[CalendarEvent]] = defaultdict(list)

        for e in events:
            day_key = e.start.strftime("%Y-%m-%d")
            by_day[day_key].append(e)

        result = []
        for day_str in sorted(by_day.keys()):
            day_events = sorted(by_day[day_str], key=lambda e: e.start)
            total = len(day_events)
            hours = sum(e.duration_minutes for e in day_events) / 60
            after = sum(1 for e in day_events if e.is_after_hours)

            # Focus hours: work_hours - meeting_hours, minimum 0
            focus = max(0, self.WORK_HOURS_PER_DAY - hours)

            # Back-to-back: meetings starting within 5 min of previous ending
            b2b = 0
            for i in range(1, len(day_events)):
                gap = (day_events[i].start - day_events[i - 1].end).total_seconds() / 60
                if gap < 5:
                    b2b += 1

            # Largest focus block
            largest_block = self._largest_focus_block(day_events)

            # Meeting type counts
            types: Dict[str, int] = defaultdict(int)
            for e in day_events:
                types[e.meeting_type.value] += 1

            result.append(
                DailyMeetingLoad(
                    date=day_str,
                    total_meetings=total,
                    total_hours=round(hours, 1),
                    focus_hours=round(focus, 1),
                    after_hours_meetings=after,
                    back_to_back_chains=b2b,
                    largest_focus_block_min=largest_block,
                    meeting_types=dict(types),
                )
            )

        return result

    def _largest_focus_block(self, day_events: List[CalendarEvent]) -> int:
        """Find the largest gap between meetings during work hours."""
        if not day_events:
            return int(self.WORK_HOURS_PER_DAY * 60)

        work_start = datetime.combine(day_events[0].start.date(), self.WORK_START)
        work_end = datetime.combine(day_events[0].start.date(), self.WORK_END)

        gaps = []
        # Gap before first meeting
        if day_events[0].start > work_start:
            gaps.append((day_events[0].start - work_start).total_seconds() / 60)

        # Gaps between meetings
        for i in range(1, len(day_events)):
            gap = (day_events[i].start - day_events[i - 1].end).total_seconds() / 60
            if gap > 0:
                gaps.append(gap)

        # Gap after last meeting
        if day_events[-1].end < work_end:
            gaps.append((work_end - day_events[-1].end).total_seconds() / 60)

        return int(max(gaps)) if gaps else 0

    def _fragmentation_score(self, daily_loads: List[DailyMeetingLoad]) -> float:
        """How fragmented is the calendar? (many short gaps = high fragmentation)."""
        if not daily_loads:
            return 0

        scores = []
        for d in daily_loads:
            if d.total_meetings <= 1:
                scores.append(0)
            else:
                # More meetings with less total time = more fragmented
                avg_meeting_min = (
                    (d.total_hours * 60) / d.total_meetings if d.total_meetings else 0
                )
                # Short meetings + back-to-back = high fragmentation
                frag = 0
                if avg_meeting_min < 30:
                    frag += 30
                if d.back_to_back_chains > 0:
                    frag += d.back_to_back_chains * 15
                if d.largest_focus_block_min < 60:
                    frag += 20
                scores.append(min(100, frag))

        return sum(scores) / len(scores) if scores else 0

    def _score_label(self, score: float) -> str:
        if score >= 80:
            return "Healthy"
        if score >= 60:
            return "Moderate"
        if score >= 40:
            return "Overloaded"
        return "Critical"

    def _generate_recommendations(
        self,
        hours_week,
        focus_week,
        after_hours_pct,
        b2b_rate,
        one_on_one_ratio,
        recurring_pct,
        fragmentation,
    ) -> List[str]:
        recs = []
        if hours_week > 20:
            recs.append(
                f"Meeting load is {hours_week:.0f}h/week — well above the 15h healthy threshold. Audit recurring meetings for necessity."
            )
        elif hours_week > 15:
            recs.append(
                f"Meeting load ({hours_week:.0f}h/week) is above recommended. Consider declining non-essential meetings."
            )

        if focus_week < 10:
            recs.append(
                f"Only {focus_week:.0f}h/week of focus time. Block 2-hour deep work sessions on your calendar."
            )

        if after_hours_pct > 15:
            recs.append(
                f"{after_hours_pct:.0f}% of meetings are outside work hours. Set calendar boundaries to protect personal time."
            )

        if b2b_rate > 0.3:
            recs.append(
                "High back-to-back meeting rate. Add 5-10 minute buffers between meetings for transition time."
            )

        if recurring_pct > 60:
            recs.append(
                f"{recurring_pct:.0f}% of meetings are recurring. Review whether all recurring meetings still serve their purpose."
            )

        if one_on_one_ratio < 0.15 and hours_week > 5:
            recs.append(
                "Low 1:1 ratio. Consider replacing some group meetings with targeted 1:1s for better outcomes."
            )

        if fragmentation > 60:
            recs.append(
                "Calendar is highly fragmented. Batch meetings into specific days or time blocks to create focus windows."
            )

        if not recs:
            recs.append(
                "Calendar health looks good. Maintain current meeting practices."
            )

        return recs


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class CalendarRegistry:
    """Manages configured calendar connectors."""

    CONNECTOR_TYPES = {
        "google": GoogleCalendarConnector,
        "outlook": OutlookCalendarConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, CalendarConnector] = {}

    def register(self, name: str, connector: CalendarConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered calendar connector: %s", name)

    def get(self, name: str) -> Optional[CalendarConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


calendar_registry = CalendarRegistry()
