"""
Endpoint / MDM Metadata Service

Analyzes device METADATA ONLY — screen lock/unlock times, app foreground
duration, idle gaps. Never reads screen content, keystrokes, or files.

Input signals (per device):
  - screen unlock/lock timestamps (actual working hours)
  - app foreground time (which categories, how long)
  - idle periods (gaps between activity)
  - OS update compliance
  - battery/charging patterns (proxy for location)

Output behavioral signals:
  - actual_screen_time (vs. calendar-declared hours)
  - break_deficit (insufficient idle gaps)
  - app_focus_duration (long uninterrupted sessions vs constant switching)
  - screen_time_trend (expanding week-over-week)
  - boundary_erosion_score
  - burnout_risk_score

Data sources: Jamf Pro API (Mac), Microsoft Intune Graph API (Windows)
"""

import logging
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════
# NORMALIZED SCHEMA
# ══════════════════════════════════════════════════════════════════


class ScreenEventType(str, Enum):
    UNLOCK = "unlock"
    LOCK = "lock"
    IDLE_START = "idle_start"
    IDLE_END = "idle_end"
    APP_SWITCH = "app_switch"


class AppCategory(str, Enum):
    PRODUCTIVITY = "productivity"  # docs, sheets, IDE
    COMMUNICATION = "communication"  # email, slack, teams
    BROWSER = "browser"
    MEETING = "meeting"  # zoom, meet, teams call
    OTHER = "other"


@dataclass
class EndpointActivityRecord:
    """One device activity event — no screen content or keystrokes."""

    user_id: str
    device_id: str
    timestamp: datetime
    event_type: ScreenEventType
    app_category: Optional[AppCategory] = None
    duration_minutes: Optional[float] = None  # for unlock-to-lock spans
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class EndpointMetadataSignals:
    """Behavioral signals derived from endpoint/MDM metadata."""

    # Screen time
    avg_daily_screen_hours: float
    screen_time_trend: float  # week-over-week change
    avg_first_unlock_hour: float
    avg_last_lock_hour: float

    # Breaks & focus
    avg_break_gap_minutes: float  # average idle gap between sessions
    break_deficit_score: float  # 0-100, insufficient breaks
    avg_focus_block_minutes: float  # avg uninterrupted work session
    app_switches_per_hour: float  # context switching proxy

    # Category distribution
    productivity_ratio: float
    communication_ratio: float
    meeting_ratio: float

    # Timing
    after_hours_ratio: float
    weekend_ratio: float

    # Composite scores (0-100)
    cognitive_load_score: float  # high switching + long hours
    boundary_erosion_score: float
    burnout_risk_score: float

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class EndpointMetadataConnector(ABC):
    """Base interface for endpoint/MDM metadata connectors.

    Connectors must NEVER capture screen content, keystrokes, file names,
    or browsing URLs. Only device state transitions and app category time.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[EndpointActivityRecord]: ...


# ══════════════════════════════════════════════════════════════════
# JAMF PRO CONNECTOR (macOS)
# ══════════════════════════════════════════════════════════════════


class JamfProConnector(EndpointMetadataConnector):
    """Jamf Pro API connector — device usage metadata only.

    Uses /JSSResource/computerhistory for login/logout events and
    application usage (category time, not specific app names).
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(self, base_url: str = "", username: str = "", password: str = ""):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.base_url and self.username),
            "provider": "jamf_pro",
            "note": "Device usage metadata — no screen content or keystrokes",
        }

    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[EndpointActivityRecord]:
        if not self.base_url:
            return []

        records: List[EndpointActivityRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get computer ID for user
                resp = await client.get(
                    f"{self.base_url}/api/v1/computers-inventory",
                    auth=(self.username, self.password),
                    headers={"Accept": "application/json"},
                    params={
                        "filter": f"general.lastContactTime>{start.isoformat()}",
                        "section": "GENERAL,HARDWARE",
                    },
                )
                resp.raise_for_status()
                computers = resp.json().get("results", [])

                for comp in computers:
                    comp_id = comp.get("id")
                    if not comp_id:
                        continue

                    # Fetch usage history
                    hist_resp = await client.get(
                        f"{self.base_url}/JSSResource/computerhistory/id/{comp_id}/subset/Usage",
                        auth=(self.username, self.password),
                        headers={"Accept": "application/json"},
                    )
                    if hist_resp.status_code != 200:
                        continue

                    usage = (
                        hist_resp.json()
                        .get("computer_history", {})
                        .get("usage_logs", [])
                    )
                    for entry in usage:
                        ts_str = entry.get("date_time", "")
                        try:
                            ts = datetime.fromisoformat(ts_str)
                        except (ValueError, TypeError):
                            continue

                        if ts < start or ts > end:
                            continue

                        event_str = entry.get("event", "").lower()
                        if "login" in event_str or "unlock" in event_str:
                            evt = ScreenEventType.UNLOCK
                        elif "logout" in event_str or "lock" in event_str:
                            evt = ScreenEventType.LOCK
                        else:
                            continue

                        records.append(
                            EndpointActivityRecord(
                                user_id=user_id,
                                device_id=str(comp_id),
                                timestamp=ts,
                                event_type=evt,
                                is_after_hours=self._is_after_hours(ts),
                                is_weekend=ts.weekday() >= 5,
                            )
                        )

            logger.info("Jamf: fetched %d events for %s", len(records), user_id)
        except ImportError:
            logger.warning("httpx not installed — Jamf connector disabled")
        except Exception as e:
            logger.error("Jamf fetch error: %s", e)
        return records

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# INTUNE CONNECTOR (Windows)
# ══════════════════════════════════════════════════════════════════


class IntuneConnector(EndpointMetadataConnector):
    """Microsoft Intune via Graph API — device activity metadata.

    Uses /deviceManagement/managedDevices for device state and
    reports/getDeviceManagementIntentPerSettingContributionProfiles
    for usage patterns. No screen recording or content access.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

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
            "connected": bool(self.tenant_id and self.client_id),
            "provider": "intune",
            "scopes": ["DeviceManagementManagedDevices.Read.All"],
            "note": "Device metadata — no screen content access",
        }

    async def fetch_activity(
        self,
        user_id: str,
        start: datetime,
        end: datetime,
    ) -> List[EndpointActivityRecord]:
        if not self.tenant_id:
            return []

        records: List[EndpointActivityRecord] = []
        try:
            import httpx

            token = await self._get_token()
            if not token:
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                # Get managed devices for user
                resp = await client.get(
                    f"{self.base_url}/users/{user_id}/managedDevices",
                    headers={"Authorization": f"Bearer {token}"},
                    params={
                        "$select": "id,deviceName,lastSyncDateTime,complianceState",
                    },
                )
                resp.raise_for_status()
                devices = resp.json().get("value", [])

                for device in devices:
                    device_id = device.get("id", "")
                    last_sync = device.get("lastSyncDateTime", "")
                    if last_sync:
                        try:
                            ts = datetime.fromisoformat(
                                last_sync.replace("Z", "+00:00")
                            )
                            if start <= ts <= end:
                                records.append(
                                    EndpointActivityRecord(
                                        user_id=user_id,
                                        device_id=device_id,
                                        timestamp=ts,
                                        event_type=ScreenEventType.UNLOCK,
                                        is_after_hours=self._is_after_hours(ts),
                                        is_weekend=ts.weekday() >= 5,
                                    )
                                )
                        except (ValueError, TypeError):
                            pass

            logger.info("Intune: fetched %d events for %s", len(records), user_id)
        except ImportError:
            logger.warning("httpx not installed — Intune connector disabled")
        except Exception as e:
            logger.error("Intune fetch error: %s", e)
        return records

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END

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
            logger.error("Intune token error: %s", e)
            return None


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class EndpointMetadataAnalyzer:
    """Extracts behavioral signals from endpoint metadata.

    Works with screen lock/unlock events and app category time.
    The most accurate source for actual working hours — captures
    when someone is truly at their device, not just calendar booked.
    """

    def analyze(
        self,
        events: List[EndpointActivityRecord],
        days: int = 14,
    ) -> EndpointMetadataSignals:
        if not events:
            return self._empty_signals()

        sorted_events = sorted(events, key=lambda e: e.timestamp)

        # Group by day
        by_day: Dict[str, List[EndpointActivityRecord]] = defaultdict(list)
        for e in sorted_events:
            by_day[e.timestamp.strftime("%Y-%m-%d")].append(e)

        # Compute screen-on sessions (unlock→lock pairs)
        sessions = self._compute_sessions(sorted_events)
        screen_hours_per_day: List[float] = []
        first_unlocks: List[float] = []
        last_locks: List[float] = []

        for day_events in by_day.values():
            day_sorted = sorted(day_events, key=lambda e: e.timestamp)
            first_unlocks.append(
                day_sorted[0].timestamp.hour + day_sorted[0].timestamp.minute / 60
            )
            last_locks.append(
                day_sorted[-1].timestamp.hour + day_sorted[-1].timestamp.minute / 60
            )

        for day_str, day_sessions in self._group_sessions_by_day(sessions).items():
            total_hours = sum(s["duration_min"] for s in day_sessions) / 60
            screen_hours_per_day.append(total_hours)

        avg_screen = (
            sum(screen_hours_per_day) / len(screen_hours_per_day)
            if screen_hours_per_day
            else 0
        )
        avg_first = sum(first_unlocks) / len(first_unlocks) if first_unlocks else 9
        avg_last = sum(last_locks) / len(last_locks) if last_locks else 17

        # Screen time trend
        screen_trend = 0.0
        if len(screen_hours_per_day) >= 4:
            mid = len(screen_hours_per_day) // 2
            first_half = sum(screen_hours_per_day[:mid]) / mid
            second_half = sum(screen_hours_per_day[mid:]) / (
                len(screen_hours_per_day) - mid
            )
            screen_trend = second_half - first_half

        # Break analysis
        break_gaps = [s["gap_before_min"] for s in sessions if s.get("gap_before_min")]
        avg_break = sum(break_gaps) / len(break_gaps) if break_gaps else 30
        break_deficit = self._break_deficit_score(break_gaps, avg_screen)

        # Focus blocks
        session_durations = [s["duration_min"] for s in sessions]
        avg_focus = (
            sum(session_durations) / len(session_durations) if session_durations else 0
        )

        # App switching
        switches = sum(
            1 for e in sorted_events if e.event_type == ScreenEventType.APP_SWITCH
        )
        active_hours = max(avg_screen * len(by_day), 1)
        switches_per_hour = switches / active_hours

        # Category distribution
        cat_time: Dict[str, float] = defaultdict(float)
        for e in sorted_events:
            if e.app_category and e.duration_minutes:
                cat_time[e.app_category.value] += e.duration_minutes
        total_cat = sum(cat_time.values()) or 1
        prod_ratio = cat_time.get("productivity", 0) / total_cat
        comm_ratio = cat_time.get("communication", 0) / total_cat
        meet_ratio = cat_time.get("meeting", 0) / total_cat

        # Timing
        ah_events = [e for e in sorted_events if e.is_after_hours]
        wk_events = [e for e in sorted_events if e.is_weekend]
        ah_ratio = len(ah_events) / max(len(sorted_events), 1)
        wk_ratio = len(wk_events) / max(len(sorted_events), 1)

        # Composite scores
        cognitive_load = self._cognitive_load_score(
            switches_per_hour, avg_screen, avg_focus
        )
        boundary = self._boundary_erosion_score(ah_ratio, wk_ratio, avg_screen)
        burnout, label = self._burnout_risk_score(
            cognitive_load, boundary, break_deficit, screen_trend, wk_ratio
        )

        daily = self._daily_breakdown(by_day, sessions)
        recs = self._generate_recommendations(
            avg_screen,
            screen_trend,
            break_deficit,
            switches_per_hour,
            ah_ratio,
            wk_ratio,
            cognitive_load,
            boundary,
        )

        return EndpointMetadataSignals(
            avg_daily_screen_hours=round(avg_screen, 1),
            screen_time_trend=round(screen_trend, 2),
            avg_first_unlock_hour=round(avg_first, 1),
            avg_last_lock_hour=round(avg_last, 1),
            avg_break_gap_minutes=round(avg_break, 1),
            break_deficit_score=round(break_deficit, 1),
            avg_focus_block_minutes=round(avg_focus, 1),
            app_switches_per_hour=round(switches_per_hour, 1),
            productivity_ratio=round(prod_ratio, 3),
            communication_ratio=round(comm_ratio, 3),
            meeting_ratio=round(meet_ratio, 3),
            after_hours_ratio=round(ah_ratio, 3),
            weekend_ratio=round(wk_ratio, 3),
            cognitive_load_score=round(cognitive_load, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    def _compute_sessions(
        self, events: List[EndpointActivityRecord]
    ) -> List[Dict[str, Any]]:
        """Pair unlock→lock events into screen-on sessions."""
        sessions = []
        last_unlock: Optional[EndpointActivityRecord] = None
        last_lock_time: Optional[datetime] = None

        for e in events:
            if e.event_type == ScreenEventType.UNLOCK:
                last_unlock = e
            elif e.event_type == ScreenEventType.LOCK and last_unlock:
                duration = (e.timestamp - last_unlock.timestamp).total_seconds() / 60
                if 0 < duration < 1440:  # sanity: max 24h
                    gap_before = None
                    if last_lock_time:
                        gap_before = (
                            last_unlock.timestamp - last_lock_time
                        ).total_seconds() / 60
                    sessions.append(
                        {
                            "start": last_unlock.timestamp,
                            "end": e.timestamp,
                            "duration_min": duration,
                            "gap_before_min": gap_before,
                            "is_after_hours": last_unlock.is_after_hours,
                        }
                    )
                    last_lock_time = e.timestamp
                last_unlock = None

        return sessions

    def _group_sessions_by_day(
        self, sessions: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        by_day: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for s in sessions:
            by_day[s["start"].strftime("%Y-%m-%d")].append(s)
        return by_day

    def _break_deficit_score(
        self, break_gaps: List[float], avg_screen_hours: float
    ) -> float:
        """0-100: are breaks insufficient for the screen time level?

        Research: 5-10 min break every 50-90 min is optimal.
        No break > 15 min in an 8+ hour day is a deficit.
        """
        if not break_gaps:
            return 50 if avg_screen_hours > 6 else 0

        # Count gaps >= 15 min (meaningful breaks)
        meaningful_breaks = sum(1 for g in break_gaps if g >= 15)
        expected_breaks = max(1, int(avg_screen_hours / 1.5))
        break_ratio = meaningful_breaks / expected_breaks

        if break_ratio >= 1.0:
            deficit = 0
        elif break_ratio >= 0.5:
            deficit = (1 - break_ratio) * 60
        else:
            deficit = 60 + (0.5 - break_ratio) * 80

        # Long screen hours with few breaks is worse
        if avg_screen_hours > 10 and meaningful_breaks < 3:
            deficit = min(100, deficit + 20)

        return min(100, deficit)

    def _cognitive_load_score(
        self,
        switches_per_hour: float,
        avg_screen: float,
        avg_focus: float,
    ) -> float:
        """0-100: cognitive overload from app switching + long hours.

        Research shows each task switch costs ~23 minutes of refocus time.
        High switching + long hours = cognitive exhaustion.
        """
        # Switching penalty: 5+/hour is high
        switch_component = min(50, max(0, switches_per_hour - 3) * 20)
        # Short focus blocks: avg < 25 min = fragmented
        focus_deficit = min(30, max(0, 25 - avg_focus) * 2) if avg_focus > 0 else 0
        # Long hours amplify switching cost
        hour_amplifier = min(20, max(0, avg_screen - 8) * 5)

        return min(100, switch_component + focus_deficit + hour_amplifier)

    def _boundary_erosion_score(
        self, ah_ratio: float, wk_ratio: float, avg_screen: float
    ) -> float:
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, wk_ratio * 400)
        screen_component = min(30, max(0, avg_screen - 9) * 10)
        return ah_component * 0.40 + wk_component * 0.35 + screen_component * 0.25

    def _burnout_risk_score(
        self,
        cognitive_load: float,
        boundary: float,
        break_deficit: float,
        screen_trend: float,
        wk_ratio: float,
    ) -> tuple:
        """Composite burnout from endpoint data. Returns (score, label).

        Endpoint data captures actual screen time — the most accurate
        measure of real working hours available from any data source.
        Break deficit is a unique signal only endpoints can provide.
        """
        base = boundary * 0.30 + cognitive_load * 0.25 + break_deficit * 0.25

        # Screen time expansion
        trend_amp = min(15, max(0, screen_trend) * 10)
        base += trend_amp * 0.20

        # Interaction
        interaction = (cognitive_load / 100) * (boundary / 100) * 20

        # Weekend screen time
        weekend_amp = min(10, max(0, (wk_ratio - 0.05) * 100))

        score = min(100, base + interaction + weekend_amp)

        if score >= 70:
            label = "Critical"
        elif score >= 45:
            label = "Elevated"
        elif score >= 25:
            label = "Monitor"
        else:
            label = "Healthy"

        return round(score, 1), label

    def _daily_breakdown(
        self,
        by_day: Dict[str, List[EndpointActivityRecord]],
        sessions: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        session_by_day = self._group_sessions_by_day(sessions)
        result = []
        for day_str in sorted(by_day.keys()):
            events = by_day[day_str]
            day_sessions = session_by_day.get(day_str, [])
            screen_hours = sum(s["duration_min"] for s in day_sessions) / 60
            breaks = [
                s["gap_before_min"] for s in day_sessions if s.get("gap_before_min")
            ]

            result.append(
                {
                    "date": day_str,
                    "screen_hours": round(screen_hours, 1),
                    "sessions": len(day_sessions),
                    "avg_break_min": (
                        round(sum(breaks) / len(breaks), 1) if breaks else 0
                    ),
                    "after_hours_events": sum(1 for e in events if e.is_after_hours),
                    "app_switches": sum(
                        1 for e in events if e.event_type == ScreenEventType.APP_SWITCH
                    ),
                }
            )
        return result

    def _generate_recommendations(
        self,
        avg_screen: float,
        trend: float,
        break_deficit: float,
        switches: float,
        ah_ratio: float,
        wk_ratio: float,
        cognitive_load: float,
        boundary: float,
    ) -> List[str]:
        recs = []
        if avg_screen > 10:
            recs.append(
                f"Average screen time is {avg_screen:.1f} hours/day — well above healthy limits. "
                "Implement hard-stop reminders."
            )
        if trend > 0.5:
            recs.append(
                f"Screen time expanding by {trend:.1f} hours/week. "
                "This trajectory leads to chronic fatigue."
            )
        if break_deficit > 50:
            recs.append(
                "Insufficient breaks detected. "
                "Enable OS break reminders (every 90 min)."
            )
        if switches > 8:
            recs.append(
                f"High app switching ({switches:.0f}/hour) causes significant cognitive drain. "
                "Batch similar tasks together."
            )
        if cognitive_load > 60:
            recs.append(
                "Cognitive load is elevated — combination of high switching and long hours. "
                "Schedule focus blocks with notifications off."
            )
        if wk_ratio > 0.10:
            recs.append(
                f"{wk_ratio*100:.0f}% of screen time is on weekends. "
                "Protect recovery time."
            )
        if boundary > 60:
            recs.append(
                "Work-life boundary erosion detected from device usage. "
                "Set up OS-level screen time limits."
            )
        if not recs:
            recs.append("Device usage patterns look healthy.")
        return recs

    def _empty_signals(self) -> EndpointMetadataSignals:
        return EndpointMetadataSignals(
            avg_daily_screen_hours=0,
            screen_time_trend=0,
            avg_first_unlock_hour=9,
            avg_last_lock_hour=17,
            avg_break_gap_minutes=0,
            break_deficit_score=0,
            avg_focus_block_minutes=0,
            app_switches_per_hour=0,
            productivity_ratio=0,
            communication_ratio=0,
            meeting_ratio=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            cognitive_load_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No endpoint data available. Connect MDM to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class EndpointMetadataRegistry:
    CONNECTOR_TYPES = {
        "jamf": JamfProConnector,
        "intune": IntuneConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, EndpointMetadataConnector] = {}

    def register(self, name: str, connector: EndpointMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered endpoint metadata connector: %s", name)

    def get(self, name: str) -> Optional[EndpointMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


endpoint_metadata_registry = EndpointMetadataRegistry()
