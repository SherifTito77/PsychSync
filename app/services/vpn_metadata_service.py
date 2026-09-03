"""
VPN / Remote Access Metadata Service

Analyzes VPN session METADATA ONLY — connection timestamps, duration,
city-level location. Never reads traffic content or browsing data.

Input signals (per session):
  - connect/disconnect timestamps
  - session duration
  - city-level location (not precise coordinates)
  - connection type (full tunnel, split tunnel)

Output behavioral signals:
  - session_duration_trend (expanding over weeks)
  - after_hours_vpn_ratio
  - weekend_vpn_ratio
  - location_anomaly_score (unusual cities = possible interviewing)
  - late_night_session_ratio
  - boundary_erosion_score
  - burnout_risk_score

Data sources: Cisco AnyConnect, GlobalProtect, Zscaler API
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


class VPNEventType(str, Enum):
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    RECONNECT = "reconnect"


@dataclass
class VPNSessionRecord:
    """One VPN session — no traffic content."""

    user_id: str
    user_email: str
    connect_time: datetime
    disconnect_time: Optional[datetime]
    duration_minutes: float
    city: Optional[str] = None
    country: Optional[str] = None
    connection_type: str = "full_tunnel"  # full_tunnel, split_tunnel
    bytes_transferred: Optional[int] = None  # aggregate only, no content
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class VPNMetadataSignals:
    """Behavioral signals derived from VPN session metadata."""

    # Session patterns
    avg_session_duration_hours: float
    session_duration_trend: float  # week-over-week change
    total_sessions: int
    avg_sessions_per_day: float

    # Timing
    after_hours_ratio: float
    weekend_ratio: float
    late_night_ratio: float  # sessions starting after 10pm
    earliest_avg_connect: float  # avg hour of first connection
    latest_avg_disconnect: float  # avg hour of last disconnection

    # Location
    unique_locations: int
    location_anomaly_score: float  # 0-100, unusual locations

    # Composite scores (0-100)
    boundary_erosion_score: float
    burnout_risk_score: float
    flight_risk_indicator: float  # unusual location patterns

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class VPNMetadataConnector(ABC):
    """Base interface for VPN metadata connectors.

    Connectors must NEVER request traffic logs, browsing history, or
    content inspection data. Only session metadata.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_sessions(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[VPNSessionRecord]: ...


# ══════════════════════════════════════════════════════════════════
# CISCO ANYCONNECT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class CiscoAnyConnectConnector(VPNMetadataConnector):
    """Cisco AnyConnect via ASA REST API — session metadata only.

    Uses /api/monitoring/vpn-sessions for active/historical sessions.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(self, base_url: str = "", api_key: str = ""):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.base_url and self.api_key),
            "provider": "cisco_anyconnect",
            "note": "VPN session metadata only — no traffic inspection",
        }

    async def fetch_sessions(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[VPNSessionRecord]:
        if not self.base_url or not self.api_key:
            return []

        records: List[VPNSessionRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/api/monitoring/vpn-sessions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json",
                    },
                    params={
                        "username": user_email,
                        "startTime": start.isoformat(),
                        "endTime": end.isoformat(),
                    },
                )
                resp.raise_for_status()
                sessions = resp.json().get("sessions", [])

                for s in sessions:
                    record = self._normalize(s, user_email)
                    if record:
                        records.append(record)

            logger.info(
                "Cisco: fetched %d VPN sessions for %s", len(records), user_email
            )
        except ImportError:
            logger.warning("httpx not installed — Cisco connector disabled")
        except Exception as e:
            logger.error("Cisco VPN fetch error: %s", e)
        return records

    def _normalize(self, session: dict, user_email: str) -> Optional[VPNSessionRecord]:
        try:
            connect = datetime.fromisoformat(session["loginTime"])
            disconnect = None
            duration = 0.0
            if session.get("logoutTime"):
                disconnect = datetime.fromisoformat(session["logoutTime"])
                duration = (disconnect - connect).total_seconds() / 60
            else:
                duration = session.get("duration", 0) / 60

            return VPNSessionRecord(
                user_id=session.get("userId", ""),
                user_email=user_email,
                connect_time=connect,
                disconnect_time=disconnect,
                duration_minutes=duration,
                city=session.get("location", {}).get("city"),
                country=session.get("location", {}).get("country"),
                connection_type=session.get("tunnelType", "full_tunnel"),
                bytes_transferred=session.get("bytesTransferred"),
                is_after_hours=self._is_after_hours(connect),
                is_weekend=connect.weekday() >= 5,
            )
        except Exception as e:
            logger.debug("Skipping VPN session: %s", e)
            return None

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# ZSCALER CONNECTOR
# ══════════════════════════════════════════════════════════════════


class ZscalerVPNConnector(VPNMetadataConnector):
    """Zscaler ZPA API — user session metadata.

    Uses /api/v1/userSessions for connection metadata.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        cloud: str = "",
        api_key: str = "",
        client_id: str = "",
        client_secret: str = "",
    ):
        self.cloud = cloud  # e.g., "zscaler.net"
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.cloud and self.api_key),
            "provider": "zscaler_zpa",
            "note": "ZPA session metadata — no content inspection",
        }

    async def fetch_sessions(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[VPNSessionRecord]:
        if not self.cloud or not self.api_key:
            return []

        records: List[VPNSessionRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"https://{self.cloud}/api/v1/userSessions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Accept": "application/json",
                    },
                    params={
                        "email": user_email,
                        "from": int(start.timestamp()),
                        "to": int(end.timestamp()),
                    },
                )
                resp.raise_for_status()
                for s in resp.json().get("sessions", []):
                    connect = datetime.fromtimestamp(s.get("startTime", 0))
                    end_time = None
                    duration = s.get("duration", 0) / 60
                    if s.get("endTime"):
                        end_time = datetime.fromtimestamp(s["endTime"])
                        duration = (end_time - connect).total_seconds() / 60

                    records.append(
                        VPNSessionRecord(
                            user_id=s.get("userId", ""),
                            user_email=user_email,
                            connect_time=connect,
                            disconnect_time=end_time,
                            duration_minutes=duration,
                            city=s.get("clientGeoLocation", {}).get("city"),
                            country=s.get("clientGeoLocation", {}).get("country"),
                            is_after_hours=self._is_after_hours(connect),
                            is_weekend=connect.weekday() >= 5,
                        )
                    )

            logger.info("Zscaler: fetched %d sessions for %s", len(records), user_email)
        except ImportError:
            logger.warning("httpx not installed — Zscaler connector disabled")
        except Exception as e:
            logger.error("Zscaler fetch error: %s", e)
        return records

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class VPNMetadataAnalyzer:
    """Extracts behavioral signals from VPN session metadata.

    Never sees traffic content. Works only with timestamps, duration,
    and city-level location.
    """

    def analyze(
        self,
        sessions: List[VPNSessionRecord],
        days: int = 14,
    ) -> VPNMetadataSignals:
        if not sessions:
            return self._empty_signals()

        # Group by day
        by_day: Dict[str, List[VPNSessionRecord]] = defaultdict(list)
        for s in sessions:
            by_day[s.connect_time.strftime("%Y-%m-%d")].append(s)

        # Duration
        durations_hrs = [s.duration_minutes / 60 for s in sessions]
        avg_duration = sum(durations_hrs) / len(durations_hrs)
        avg_per_day = len(sessions) / max(days, 1)

        # Duration trend
        duration_trend = 0.0
        if len(durations_hrs) >= 4:
            mid = len(durations_hrs) // 2
            first_half = sum(durations_hrs[:mid]) / mid
            second_half = sum(durations_hrs[mid:]) / (len(durations_hrs) - mid)
            duration_trend = second_half - first_half

        # Timing
        after_hours = [s for s in sessions if s.is_after_hours]
        weekend = [s for s in sessions if s.is_weekend]
        late_night = [
            s for s in sessions if s.connect_time.hour >= 22 or s.connect_time.hour < 5
        ]
        ah_ratio = len(after_hours) / max(len(sessions), 1)
        wk_ratio = len(weekend) / max(len(sessions), 1)
        ln_ratio = len(late_night) / max(len(sessions), 1)

        # Earliest/latest
        connect_hours = [
            s.connect_time.hour + s.connect_time.minute / 60 for s in sessions
        ]
        disconnect_hours = []
        for s in sessions:
            if s.disconnect_time:
                disconnect_hours.append(
                    s.disconnect_time.hour + s.disconnect_time.minute / 60
                )
        avg_connect = sum(connect_hours) / len(connect_hours)
        avg_disconnect = (
            sum(disconnect_hours) / len(disconnect_hours) if disconnect_hours else 17
        )

        # Location analysis
        cities = set(s.city for s in sessions if s.city)

        # Location anomaly: frequent city vs unusual appearances
        city_counts: Dict[str, int] = defaultdict(int)
        for s in sessions:
            if s.city:
                city_counts[s.city] += 1
        location_anomaly = self._location_anomaly_score(city_counts, len(sessions))

        # Composite scores
        boundary = self._boundary_erosion_score(
            ah_ratio, wk_ratio, ln_ratio, avg_duration
        )
        burnout, label = self._burnout_risk_score(
            boundary, duration_trend, ah_ratio, wk_ratio, avg_duration
        )
        flight_risk = self._flight_risk_score(
            location_anomaly, wk_ratio, duration_trend
        )

        daily = self._daily_breakdown(by_day)
        recs = self._generate_recommendations(
            avg_duration,
            duration_trend,
            ah_ratio,
            wk_ratio,
            ln_ratio,
            location_anomaly,
            boundary,
        )

        return VPNMetadataSignals(
            avg_session_duration_hours=round(avg_duration, 1),
            session_duration_trend=round(duration_trend, 2),
            total_sessions=len(sessions),
            avg_sessions_per_day=round(avg_per_day, 1),
            after_hours_ratio=round(ah_ratio, 3),
            weekend_ratio=round(wk_ratio, 3),
            late_night_ratio=round(ln_ratio, 3),
            earliest_avg_connect=round(avg_connect, 1),
            latest_avg_disconnect=round(avg_disconnect, 1),
            unique_locations=len(cities),
            location_anomaly_score=round(location_anomaly, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            flight_risk_indicator=round(flight_risk, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    def _location_anomaly_score(self, city_counts: Dict[str, int], total: int) -> float:
        """0-100: how unusual are the login locations?

        One dominant city is normal. Multiple infrequent cities is anomalous.
        Could indicate interviewing at other companies or unusual travel.
        """
        if not city_counts or total == 0:
            return 0
        if len(city_counts) <= 1:
            return 0

        sorted_cities = sorted(city_counts.values(), reverse=True)
        primary_ratio = sorted_cities[0] / total
        # More non-primary cities = higher anomaly
        anomaly_cities = len(sorted_cities) - 1
        non_primary_ratio = 1 - primary_ratio

        return min(100, non_primary_ratio * 80 + anomaly_cities * 10)

    def _boundary_erosion_score(
        self,
        ah_ratio: float,
        wk_ratio: float,
        ln_ratio: float,
        avg_duration: float,
    ) -> float:
        """0-100: VPN-specific boundary erosion."""
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, wk_ratio * 400)
        ln_component = min(100, ln_ratio * 500)
        duration_component = min(30, max(0, avg_duration - 8) * 10)

        return (
            ah_component * 0.30
            + wk_component * 0.25
            + ln_component * 0.25
            + duration_component * 0.20
        )

    def _burnout_risk_score(
        self,
        boundary: float,
        duration_trend: float,
        ah_ratio: float,
        wk_ratio: float,
        avg_duration: float,
    ) -> tuple:
        """Composite burnout from VPN patterns. Returns (score, label).

        VPN uniquely captures remote work hours with high accuracy.
        Duration trend is the strongest signal — expanding sessions
        week over week indicate creeping overwork.
        """
        trend_score = min(40, max(0, duration_trend) * 20)

        base = boundary * 0.45 + trend_score * 0.30

        # Long sessions (>10h average)
        duration_amp = min(20, max(0, avg_duration - 10) * 10)
        base += duration_amp * 0.25

        # Interaction
        interaction = (boundary / 100) * (trend_score / 40) * 15

        score = min(100, base + interaction)

        if score >= 70:
            label = "Critical"
        elif score >= 45:
            label = "Elevated"
        elif score >= 25:
            label = "Monitor"
        else:
            label = "Healthy"

        return round(score, 1), label

    def _flight_risk_score(
        self, location_anomaly: float, wk_ratio: float, duration_trend: float
    ) -> float:
        """0-100: flight risk indicator from VPN location patterns.

        Unusual locations + declining engagement is a strong signal.
        """
        base = location_anomaly * 0.60
        # Declining duration trend (working less) + location changes
        if duration_trend < -0.5:
            base += min(25, abs(duration_trend) * 10)
        # Weekend work decline after sustained period is disengagement
        if wk_ratio < 0.02:
            base += 15

        return min(100, base)

    def _daily_breakdown(
        self, by_day: Dict[str, List[VPNSessionRecord]]
    ) -> List[Dict[str, Any]]:
        result = []
        for day_str in sorted(by_day.keys()):
            sessions = by_day[day_str]
            durations = [s.duration_minutes / 60 for s in sessions]
            result.append(
                {
                    "date": day_str,
                    "sessions": len(sessions),
                    "total_hours": round(sum(durations), 1),
                    "avg_duration_hours": round(sum(durations) / len(durations), 1),
                    "after_hours": sum(1 for s in sessions if s.is_after_hours),
                    "unique_locations": len(set(s.city for s in sessions if s.city)),
                }
            )
        return result

    def _generate_recommendations(
        self,
        avg_duration: float,
        trend: float,
        ah_ratio: float,
        wk_ratio: float,
        ln_ratio: float,
        location_anomaly: float,
        boundary: float,
    ) -> List[str]:
        recs = []
        if avg_duration > 10:
            recs.append(
                f"Average VPN session is {avg_duration:.1f} hours — indicates extended remote work. "
                "Set clear start/end times for remote days."
            )
        if trend > 1.0:
            recs.append(
                f"VPN session duration is expanding by {trend:.1f} hours/week. "
                "This trajectory strongly predicts burnout."
            )
        if ln_ratio > 0.15:
            recs.append(
                f"{ln_ratio*100:.0f}% of VPN sessions start after 10 PM. "
                "Late-night work disrupts sleep and recovery."
            )
        if wk_ratio > 0.15:
            recs.append(
                f"{wk_ratio*100:.0f}% of VPN sessions are on weekends. "
                "Sustained weekend work is a top burnout predictor."
            )
        if location_anomaly > 50:
            recs.append(
                "Multiple unusual login locations detected. "
                "Review whether this indicates travel stress or disengagement."
            )
        if boundary > 60:
            recs.append(
                "Remote work boundary erosion is high. "
                "Establish VPN auto-disconnect policies after work hours."
            )
        if not recs:
            recs.append("VPN usage patterns look healthy.")
        return recs

    def _empty_signals(self) -> VPNMetadataSignals:
        return VPNMetadataSignals(
            avg_session_duration_hours=0,
            session_duration_trend=0,
            total_sessions=0,
            avg_sessions_per_day=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            late_night_ratio=0,
            earliest_avg_connect=9,
            latest_avg_disconnect=17,
            unique_locations=0,
            location_anomaly_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            flight_risk_indicator=0,
            risk_label="No Data",
            recommendations=[
                "No VPN data available. Connect your VPN gateway to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class VPNMetadataRegistry:
    CONNECTOR_TYPES = {
        "cisco_anyconnect": CiscoAnyConnectConnector,
        "zscaler": ZscalerVPNConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, VPNMetadataConnector] = {}

    def register(self, name: str, connector: VPNMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered VPN metadata connector: %s", name)

    def get(self, name: str) -> Optional[VPNMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


vpn_metadata_registry = VPNMetadataRegistry()
