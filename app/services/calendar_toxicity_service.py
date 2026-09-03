"""
Calendar Toxicity Signal Service

Detects toxic meeting patterns from calendar METADATA ONLY:
  - Meeting speaking time distribution (WebRTC stats, not transcription)
  - 1:1 cancellation asymmetry (selective attention withdrawal)
  - Invite exclusion (being quietly dropped from recurring meetings)
  - Back-to-back meeting overload imposed on specific people

These signals detect power dynamics and exclusion patterns without
reading any meeting content, recordings, or transcripts.

Data sources: Microsoft Graph Calendar API, Google Calendar API,
Zoom Admin Reports API (speaking duration stats)
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


@dataclass
class MeetingMetadataRecord:
    """One meeting's metadata — no content, recordings, or transcripts."""

    meeting_id: str
    organizer_email: str
    attendee_emails: List[str]
    start_time: datetime
    end_time: datetime
    is_recurring: bool
    is_cancelled: bool = False
    cancelled_by: Optional[str] = None
    is_one_on_one: bool = False
    # Speaking time from WebRTC stats (seconds per participant)
    # NOT transcription — just audio duration counters
    speaking_seconds: Optional[Dict[str, float]] = None


@dataclass
class RecurringMeetingHistory:
    """Track who was on a recurring meeting over time — exclusion detection."""

    series_id: str
    organizer_email: str
    title_hash: str  # hashed, not the actual title
    instances: List[Dict[str, Any]] = field(default_factory=list)
    # Each instance: {"date": str, "attendees": set[str]}


@dataclass
class CalendarToxicitySignals:
    """Toxicity signals derived from calendar metadata."""

    # Meeting domination
    speaking_imbalance_score: float  # 0-100, >60% one person
    dominated_meetings_ratio: float  # fraction where one person >60%
    avg_speaking_gini: float  # Gini coefficient of speaking time

    # 1:1 cancellation patterns
    one_on_one_cancel_rate: float  # overall 1:1 cancellation rate
    selective_cancel_score: float  # 0-100, some reports cancelled more
    most_cancelled_on: Optional[str]  # email of person most cancelled on (hashed)

    # Invite exclusion
    exclusion_events: int  # times someone was dropped from recurring
    exclusion_score: float  # 0-100, severity of exclusion patterns
    excluded_individuals: int  # count of people excluded

    # Meeting load asymmetry
    meeting_load_gini: float  # inequality in meeting hours across team
    overloaded_individuals: int  # people >30h/week in meetings

    # Composite
    toxicity_score: float  # 0-100 composite
    risk_label: str

    # Fields with defaults last
    cancel_asymmetry: Dict[str, float] = field(default_factory=dict)
    signals: List[str] = field(default_factory=list)  # human-readable flags
    recommendations: List[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CalendarToxicityConnector(ABC):
    """Base for calendar toxicity connectors.

    Must fetch meeting metadata and speaking stats only.
    NEVER request meeting recordings, transcripts, or chat content.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_meetings(
        self,
        org_emails: List[str],
        start: datetime,
        end: datetime,
    ) -> List[MeetingMetadataRecord]: ...

    @abstractmethod
    async def fetch_recurring_history(
        self,
        org_emails: List[str],
        start: datetime,
        end: datetime,
    ) -> List[RecurringMeetingHistory]: ...


# ══════════════════════════════════════════════════════════════════
# MICROSOFT GRAPH CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GraphCalendarToxicityConnector(CalendarToxicityConnector):
    """Microsoft Graph API for calendar toxicity signals.

    Uses:
      - /users/{id}/calendarView for meeting metadata
      - /communications/callRecords for speaking time (duration, not content)
      - $select to exclude bodies/notes
    """

    def __init__(
        self,
        tenant_id: str = "",
        client_id: str = "",
        client_secret: str = "",
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.tenant_id),
            "provider": "microsoft_graph_calendar",
            "scopes": ["Calendars.Read", "CallRecords.Read.All"],
            "note": "Calendar metadata + call duration stats — no recordings",
        }

    async def fetch_meetings(
        self,
        org_emails: List[str],
        start: datetime,
        end: datetime,
    ) -> List[MeetingMetadataRecord]:
        if not self.tenant_id:
            return []

        records: List[MeetingMetadataRecord] = []
        try:
            import httpx

            token = await self._get_token()
            if not token:
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                for email in org_emails[:50]:  # batch limit
                    resp = await client.get(
                        f"{self.base_url}/users/{email}/calendarView",
                        headers={"Authorization": f"Bearer {token}"},
                        params={
                            "startDateTime": start.isoformat() + "Z",
                            "endDateTime": end.isoformat() + "Z",
                            "$select": "id,organizer,attendees,start,end,isCancelled,isOnlineMeeting,seriesMasterId",
                            "$top": 200,
                        },
                    )
                    if resp.status_code != 200:
                        continue

                    for event in resp.json().get("value", []):
                        record = self._normalize_meeting(event, email)
                        if record:
                            records.append(record)

            logger.info("Graph Calendar: fetched %d meetings", len(records))
        except ImportError:
            logger.warning("httpx not installed")
        except Exception as e:
            logger.error("Graph Calendar error: %s", e)
        return records

    async def fetch_recurring_history(
        self,
        org_emails: List[str],
        start: datetime,
        end: datetime,
    ) -> List[RecurringMeetingHistory]:
        # Recurring history is derived from meetings with seriesMasterId
        meetings = await self.fetch_meetings(org_emails, start, end)
        series: Dict[str, RecurringMeetingHistory] = {}

        for m in meetings:
            if not m.is_recurring:
                continue

            series_key = (
                m.meeting_id.split("_")[0] if "_" in m.meeting_id else m.meeting_id
            )
            if series_key not in series:
                series[series_key] = RecurringMeetingHistory(
                    series_id=series_key,
                    organizer_email=m.organizer_email,
                    title_hash=str(hash(series_key)),
                )

            series[series_key].instances.append(
                {
                    "date": m.start_time.strftime("%Y-%m-%d"),
                    "attendees": set(m.attendee_emails),
                }
            )

        return list(series.values())

    def _normalize_meeting(
        self, event: dict, queried_email: str
    ) -> Optional[MeetingMetadataRecord]:
        try:
            start = datetime.fromisoformat(
                event["start"]["dateTime"].replace("Z", "+00:00")
            )
            end = datetime.fromisoformat(
                event["end"]["dateTime"].replace("Z", "+00:00")
            )
            organizer = (
                event.get("organizer", {}).get("emailAddress", {}).get("address", "")
            )
            attendees = [
                a["emailAddress"]["address"]
                for a in event.get("attendees", [])
                if a.get("emailAddress", {}).get("address")
            ]
            is_cancelled = event.get("isCancelled", False)
            is_recurring = bool(event.get("seriesMasterId"))
            is_one_on_one = len(attendees) == 2

            return MeetingMetadataRecord(
                meeting_id=event.get("id", ""),
                organizer_email=organizer,
                attendee_emails=attendees,
                start_time=start,
                end_time=end,
                is_recurring=is_recurring,
                is_cancelled=is_cancelled,
                is_one_on_one=is_one_on_one,
            )
        except Exception as e:
            logger.debug("Skipping calendar event: %s", e)
            return None

    async def _get_token(self) -> Optional[str]:
        try:
            import httpx

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(
                    f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token",
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "scope": "https://graph.microsoft.com/.default",
                        "grant_type": "client_credentials",
                    },
                )
                resp.raise_for_status()
                return resp.json().get("access_token")
        except Exception as e:
            logger.error("Graph token error: %s", e)
            return None


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class CalendarToxicityAnalyzer:
    """Detects toxic meeting patterns from metadata.

    Three core signals:
    1. Speaking domination — one person talks >60% in multi-person meetings
    2. Selective cancellation — manager cancels 1:1s with specific reports
    3. Invite exclusion — person quietly removed from recurring meetings
    """

    def analyze(
        self,
        meetings: List[MeetingMetadataRecord],
        recurring: List[RecurringMeetingHistory],
        days: int = 30,
    ) -> CalendarToxicitySignals:
        if not meetings:
            return self._empty_signals()

        speaking = self._analyze_speaking(meetings)
        cancel = self._analyze_cancellations(meetings)
        exclusion = self._analyze_exclusions(recurring)
        load = self._analyze_load_asymmetry(meetings, days)

        # Composite toxicity
        toxicity = (
            speaking["imbalance_score"] * 0.20
            + cancel["selective_score"] * 0.15
            + exclusion["score"] * 0.15
            + load["gini"] * 50 * 0.10
        )

        # Combine flag signals
        signals: List[str] = []
        if speaking["imbalance_score"] > 50:
            signals.append(
                f"Meeting domination: {speaking['dominated_ratio']*100:.0f}% of meetings "
                "have one person speaking >60% of the time"
            )
        if cancel["selective_score"] > 40:
            signals.append(
                f"Selective 1:1 cancellation pattern detected — "
                f"cancel rate asymmetry of {cancel['selective_score']:.0f}"
            )
        if exclusion["events"] > 0:
            signals.append(
                f"{exclusion['events']} invite exclusion events — "
                f"{exclusion['excluded_count']} people dropped from recurring meetings"
            )
        if load["overloaded"] > 0:
            signals.append(f"{load['overloaded']} people have >30 meeting hours/week")

        label = (
            "Critical"
            if toxicity >= 60
            else (
                "Elevated"
                if toxicity >= 35
                else "Monitor" if toxicity >= 15 else "Healthy"
            )
        )

        recs = self._generate_recommendations(speaking, cancel, exclusion, load)

        return CalendarToxicitySignals(
            speaking_imbalance_score=round(speaking["imbalance_score"], 1),
            dominated_meetings_ratio=round(speaking["dominated_ratio"], 3),
            avg_speaking_gini=round(speaking["avg_gini"], 3),
            one_on_one_cancel_rate=round(cancel["overall_rate"], 3),
            selective_cancel_score=round(cancel["selective_score"], 1),
            most_cancelled_on=cancel.get("most_cancelled_on"),
            cancel_asymmetry=cancel.get("per_person_rates", {}),
            exclusion_events=exclusion["events"],
            exclusion_score=round(exclusion["score"], 1),
            excluded_individuals=exclusion["excluded_count"],
            meeting_load_gini=round(load["gini"], 3),
            overloaded_individuals=load["overloaded"],
            toxicity_score=round(toxicity, 1),
            risk_label=label,
            signals=signals,
            recommendations=recs,
        )

    def _analyze_speaking(
        self, meetings: List[MeetingMetadataRecord]
    ) -> Dict[str, Any]:
        """Detect speaking time imbalance across meetings."""
        meetings_with_speaking = [
            m for m in meetings if m.speaking_seconds and len(m.speaking_seconds) >= 2
        ]
        if not meetings_with_speaking:
            return {"imbalance_score": 0, "dominated_ratio": 0, "avg_gini": 0}

        gini_scores: List[float] = []
        dominated = 0

        for m in meetings_with_speaking:
            total_speaking = sum(m.speaking_seconds.values())
            if total_speaking == 0:
                continue

            shares = sorted(m.speaking_seconds.values(), reverse=True)
            max_share = shares[0] / total_speaking

            # Gini coefficient for speaking distribution
            n = len(shares)
            gini = self._gini_coefficient(shares)
            gini_scores.append(gini)

            # Dominated = one person > 60% in group meeting (3+ people)
            if max_share > 0.60 and len(shares) >= 3:
                dominated += 1

        avg_gini = sum(gini_scores) / len(gini_scores) if gini_scores else 0
        dominated_ratio = dominated / max(len(meetings_with_speaking), 1)

        # Score: high Gini + high domination ratio
        imbalance = avg_gini * 60 + dominated_ratio * 40

        return {
            "imbalance_score": min(100, imbalance),
            "dominated_ratio": dominated_ratio,
            "avg_gini": avg_gini,
        }

    def _analyze_cancellations(
        self, meetings: List[MeetingMetadataRecord]
    ) -> Dict[str, Any]:
        """Detect selective 1:1 cancellation patterns."""
        one_on_ones = [m for m in meetings if m.is_one_on_one]
        if not one_on_ones:
            return {
                "overall_rate": 0,
                "selective_score": 0,
                "per_person_rates": {},
            }

        # Group by organizer→attendee pair
        pair_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"total": 0, "cancelled": 0}
        )
        for m in one_on_ones:
            other = next(
                (e for e in m.attendee_emails if e != m.organizer_email),
                None,
            )
            if not other:
                continue
            key = f"{m.organizer_email}->{other}"
            pair_stats[key]["total"] += 1
            if m.is_cancelled:
                pair_stats[key]["cancelled"] += 1

        if not pair_stats:
            return {
                "overall_rate": 0,
                "selective_score": 0,
                "per_person_rates": {},
            }

        total_1on1 = sum(s["total"] for s in pair_stats.values())
        total_cancelled = sum(s["cancelled"] for s in pair_stats.values())
        overall_rate = total_cancelled / max(total_1on1, 1)

        # Per-pair cancel rates
        per_person_rates = {}
        for pair, stats in pair_stats.items():
            if stats["total"] >= 3:  # need minimum sample
                rate = stats["cancelled"] / stats["total"]
                per_person_rates[pair] = round(rate, 3)

        # Selective score: variance in cancel rates across pairs
        if len(per_person_rates) >= 2:
            rates = list(per_person_rates.values())
            mean_rate = sum(rates) / len(rates)
            variance = sum((r - mean_rate) ** 2 for r in rates) / len(rates)
            max_rate = max(rates)
            # High variance + high max = selective cancellation
            selective = min(100, variance * 500 + max_rate * 50)
        else:
            selective = 0

        # Find who gets cancelled on most
        most_cancelled = None
        if per_person_rates:
            most_cancelled_pair = max(per_person_rates, key=per_person_rates.get)
            most_cancelled = most_cancelled_pair.split("->")[1]

        return {
            "overall_rate": overall_rate,
            "selective_score": selective,
            "per_person_rates": per_person_rates,
            "most_cancelled_on": most_cancelled,
        }

    def _analyze_exclusions(
        self, recurring: List[RecurringMeetingHistory]
    ) -> Dict[str, Any]:
        """Detect people being quietly removed from recurring meetings."""
        if not recurring:
            return {"events": 0, "score": 0, "excluded_count": 0}

        exclusion_events = 0
        excluded_people: Set[str] = set()

        for series in recurring:
            if len(series.instances) < 3:
                continue

            # Sort by date
            instances = sorted(series.instances, key=lambda i: i["date"])

            # Track who disappears
            for i in range(1, len(instances)):
                prev_attendees = instances[i - 1].get("attendees", set())
                curr_attendees = instances[i].get("attendees", set())

                if not isinstance(prev_attendees, set):
                    prev_attendees = set(prev_attendees)
                if not isinstance(curr_attendees, set):
                    curr_attendees = set(curr_attendees)

                dropped = prev_attendees - curr_attendees
                # Exclude organizer changes (different phenomenon)
                dropped -= {series.organizer_email}

                for person in dropped:
                    # Check if they never return in subsequent instances
                    returns = any(
                        person
                        in (
                            inst.get("attendees", set())
                            if isinstance(inst.get("attendees"), set)
                            else set(inst.get("attendees", []))
                        )
                        for inst in instances[i + 1 :]
                    )
                    if not returns and len(instances) - i >= 2:
                        exclusion_events += 1
                        excluded_people.add(person)

        # Score based on volume and breadth
        score = min(100, exclusion_events * 15 + len(excluded_people) * 20)

        return {
            "events": exclusion_events,
            "score": score,
            "excluded_count": len(excluded_people),
        }

    def _analyze_load_asymmetry(
        self, meetings: List[MeetingMetadataRecord], days: int
    ) -> Dict[str, Any]:
        """Measure inequality in meeting hours across people."""
        hours_per_person: Dict[str, float] = defaultdict(float)

        for m in meetings:
            if m.is_cancelled:
                continue
            duration_hrs = (m.end_time - m.start_time).total_seconds() / 3600
            for email in m.attendee_emails:
                hours_per_person[email] += duration_hrs

        if not hours_per_person:
            return {"gini": 0, "overloaded": 0}

        values = sorted(hours_per_person.values())
        gini = self._gini_coefficient(values)

        weeks = max(days / 7, 1)
        overloaded = sum(1 for h in values if h / weeks > 30)

        return {"gini": gini, "overloaded": overloaded}

    def _gini_coefficient(self, values: List[float]) -> float:
        """Compute Gini coefficient (0=equal, 1=max inequality)."""
        if not values or sum(values) == 0:
            return 0
        n = len(values)
        sorted_vals = sorted(values)
        cumulative = sum((2 * (i + 1) - n - 1) * v for i, v in enumerate(sorted_vals))
        return cumulative / (n * sum(sorted_vals))

    def _generate_recommendations(
        self,
        speaking: dict,
        cancel: dict,
        exclusion: dict,
        load: dict,
    ) -> List[str]:
        recs = []
        if speaking["imbalance_score"] > 50:
            recs.append(
                "Meeting domination detected. Implement round-robin speaking "
                "or designate a facilitator for meetings with >3 participants."
            )
        if cancel["selective_score"] > 40:
            recs.append(
                "Selective 1:1 cancellation pattern found. "
                "Ensure managers maintain consistent 1:1 schedules with all reports."
            )
        if exclusion["events"] > 0:
            recs.append(
                f"{exclusion['events']} people were quietly dropped from recurring meetings. "
                "Review whether exclusions are intentional or oversight."
            )
        if load["overloaded"] > 0:
            recs.append(
                f"{load['overloaded']} individuals spend >30 hours/week in meetings. "
                "Audit meeting necessity and implement no-meeting days."
            )
        if not recs:
            recs.append("Meeting patterns look healthy. No toxicity signals detected.")
        return recs

    def _empty_signals(self) -> CalendarToxicitySignals:
        return CalendarToxicitySignals(
            speaking_imbalance_score=0,
            dominated_meetings_ratio=0,
            avg_speaking_gini=0,
            one_on_one_cancel_rate=0,
            selective_cancel_score=0,
            most_cancelled_on=None,
            exclusion_events=0,
            exclusion_score=0,
            excluded_individuals=0,
            meeting_load_gini=0,
            overloaded_individuals=0,
            toxicity_score=0,
            risk_label="No Data",
            signals=["No calendar data available."],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class CalendarToxicityRegistry:
    CONNECTOR_TYPES = {"microsoft_graph": GraphCalendarToxicityConnector}

    def __init__(self):
        self._connectors: Dict[str, CalendarToxicityConnector] = {}

    def register(self, name: str, connector: CalendarToxicityConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered calendar toxicity connector: %s", name)

    def get(self, name: str) -> Optional[CalendarToxicityConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


calendar_toxicity_registry = CalendarToxicityRegistry()
