"""
SSO / Identity Provider Metadata Service

Analyzes authentication METADATA ONLY — login timestamps, app access,
session duration. Never reads credentials, tokens, or user content.

Input signals (per user):
  - login timestamp (first/last daily)
  - app accessed (which SaaS tools)
  - session duration
  - login location (city-level, not precise)
  - auth method (SSO, MFA, password)
  - weekend/after-hours logins

Output behavioral signals:
  - login_span (first-to-last daily login hours)
  - app_switching_frequency (distinct apps per hour)
  - weekend_login_ratio
  - after_hours_login_ratio
  - session_overextension (login span expanding week-over-week)
  - boundary_erosion_score
  - burnout_risk_score

Data sources: Okta System Log API, Azure AD Sign-in Logs, Google Workspace Admin
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


class AuthEventType(str, Enum):
    LOGIN = "login"
    LOGOUT = "logout"
    APP_ACCESS = "app_access"
    MFA_CHALLENGE = "mfa_challenge"
    SESSION_REFRESH = "session_refresh"


@dataclass
class SSOEventRecord:
    """One authentication event — no credentials or tokens."""

    user_id: str
    user_email: str
    timestamp: datetime
    event_type: AuthEventType
    app_name: str  # which application was accessed
    session_id: Optional[str] = None
    ip_city: Optional[str] = None  # city-level only, no precise coords
    auth_method: str = "sso"  # sso, mfa, password
    success: bool = True
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class DailySSOSummary:
    """Per-day SSO summary."""

    date: str
    first_login: Optional[str]  # HH:MM
    last_activity: Optional[str]  # HH:MM
    login_span_hours: float
    total_logins: int
    unique_apps: int
    after_hours_logins: int
    weekend_logins: int
    failed_logins: int


@dataclass
class SSOMetadataSignals:
    """Behavioral signals derived from SSO/IdP metadata."""

    # Session patterns
    avg_login_span_hours: float  # avg first-to-last daily activity
    login_span_trend: float  # week-over-week change (positive = expanding)
    avg_first_login_hour: float  # avg hour of first daily login
    avg_last_activity_hour: float  # avg hour of last daily activity

    # App usage
    unique_apps_accessed: int
    avg_apps_per_day: float
    app_switching_rate: float  # distinct apps per active hour

    # Timing
    after_hours_ratio: float  # 0-1
    weekend_ratio: float  # 0-1
    peak_login_hour: int

    # Anomalies
    failed_login_ratio: float
    location_changes: int  # distinct cities in period

    # Composite scores (0-100)
    session_overextension_score: float
    boundary_erosion_score: float
    burnout_risk_score: float

    # Output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class SSOMetadataConnector(ABC):
    """Base interface for SSO/IdP metadata connectors.

    Connectors must NEVER request or return credentials, tokens, or
    session content. Only timestamps, app names, and city-level location.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[SSOEventRecord]: ...


# ══════════════════════════════════════════════════════════════════
# OKTA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class OktaSSOConnector(SSOMetadataConnector):
    """Okta System Log API connector — authentication events only.

    Uses /api/v1/logs with event type filters for login/app access.
    Scopes: okta.logs.read
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)
    # Okta event types for authentication
    LOGIN_EVENTS = {
        "user.session.start",
        "user.authentication.sso",
        "app.auth.sso",
    }
    APP_ACCESS_EVENTS = {
        "app.generic.unauth_app_access_attempt",
        "application.lifecycle.activate",
    }

    def __init__(self, domain: str = "", api_token: str = ""):
        self.domain = domain  # e.g., "company.okta.com"
        self.api_token = api_token

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": bool(self.domain and self.api_token),
            "provider": "okta",
            "scopes": ["okta.logs.read"],
            "note": "System Log API — auth events only, no user content",
        }

    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[SSOEventRecord]:
        if not self.domain or not self.api_token:
            return []

        records: List[SSOEventRecord] = []
        try:
            import httpx

            base_url = f"https://{self.domain}/api/v1/logs"
            params = {
                "since": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "until": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "filter": f'actor.alternateId eq "{user_email}"',
                "limit": 1000,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                url: Optional[str] = base_url
                while url:
                    resp = await client.get(
                        url,
                        headers={
                            "Authorization": f"SSWS {self.api_token}",
                            "Accept": "application/json",
                        },
                        params=params if url == base_url else None,
                    )
                    resp.raise_for_status()
                    events = resp.json()

                    for event in events:
                        record = self._normalize_event(event, user_email)
                        if record:
                            records.append(record)

                    # Okta pagination via Link header
                    link_header = resp.headers.get("link", "")
                    url = None
                    if 'rel="next"' in link_header:
                        for part in link_header.split(","):
                            if 'rel="next"' in part:
                                url = part.split(";")[0].strip().strip("<>")

            logger.info("Okta: fetched %d events for %s", len(records), user_email)
        except ImportError:
            logger.warning("httpx not installed — Okta connector disabled")
        except Exception as e:
            logger.error("Okta fetch error for %s: %s", user_email, e)
        return records

    def _normalize_event(
        self, event: dict, user_email: str
    ) -> Optional[SSOEventRecord]:
        try:
            ts = datetime.fromisoformat(event["published"].replace("Z", "+00:00"))
            event_type_str = event.get("eventType", "")

            if event_type_str in self.LOGIN_EVENTS:
                evt_type = AuthEventType.LOGIN
            elif event_type_str in self.APP_ACCESS_EVENTS:
                evt_type = AuthEventType.APP_ACCESS
            elif "mfa" in event_type_str.lower():
                evt_type = AuthEventType.MFA_CHALLENGE
            else:
                evt_type = AuthEventType.APP_ACCESS

            # App name from target
            targets = event.get("target", [])
            app_name = "unknown"
            for t in targets:
                if t.get("type") == "AppInstance":
                    app_name = t.get("displayName", "unknown")
                    break

            # Location (city only)
            geo = event.get("client", {}).get("geographicalContext", {})
            city = geo.get("city")

            # Success/failure
            outcome = event.get("outcome", {})
            success = outcome.get("result", "SUCCESS") == "SUCCESS"

            return SSOEventRecord(
                user_id=event.get("actor", {}).get("id", ""),
                user_email=user_email,
                timestamp=ts,
                event_type=evt_type,
                app_name=app_name,
                session_id=event.get("authenticationContext", {}).get(
                    "externalSessionId"
                ),
                ip_city=city,
                auth_method="mfa" if evt_type == AuthEventType.MFA_CHALLENGE else "sso",
                success=success,
                is_after_hours=self._is_after_hours(ts),
                is_weekend=ts.weekday() >= 5,
            )
        except Exception as e:
            logger.debug("Skipping Okta event: %s", e)
            return None

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# AZURE AD CONNECTOR
# ══════════════════════════════════════════════════════════════════


class AzureADSSOConnector(SSOMetadataConnector):
    """Microsoft Graph API — sign-in logs.

    Uses /auditLogs/signIns with $select for metadata only.
    Permission: AuditLog.Read.All (application)
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
            "provider": "azure_ad",
            "scopes": ["AuditLog.Read.All"],
            "note": "Sign-in logs only — no mail or file access",
        }

    async def fetch_events(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[SSOEventRecord]:
        if not self.tenant_id:
            return []

        records: List[SSOEventRecord] = []
        try:
            import httpx

            token = await self._get_token()
            if not token:
                return []

            async with httpx.AsyncClient(timeout=30.0) as client:
                url: Optional[str] = f"{self.base_url}/auditLogs/signIns"
                params = {
                    "$filter": (
                        f"userPrincipalName eq '{user_email}' "
                        f"and createdDateTime ge {start.isoformat()}Z "
                        f"and createdDateTime le {end.isoformat()}Z"
                    ),
                    "$select": "createdDateTime,appDisplayName,status,location,clientAppUsed",
                    "$top": 500,
                    "$orderby": "createdDateTime desc",
                }

                while url:
                    resp = await client.get(
                        url,
                        headers={"Authorization": f"Bearer {token}"},
                        params=params if "auditLogs" in url else None,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for item in data.get("value", []):
                        record = self._normalize(item, user_email)
                        if record:
                            records.append(record)

                    url = data.get("@odata.nextLink")

            logger.info(
                "Azure AD: fetched %d sign-ins for %s", len(records), user_email
            )
        except ImportError:
            logger.warning("httpx not installed — Azure AD connector disabled")
        except Exception as e:
            logger.error("Azure AD fetch error: %s", e)
        return records

    def _normalize(self, item: dict, user_email: str) -> Optional[SSOEventRecord]:
        try:
            ts = datetime.fromisoformat(item["createdDateTime"].replace("Z", "+00:00"))
            status = item.get("status", {})
            success = status.get("errorCode", 0) == 0

            city = item.get("location", {}).get("city")
            app_name = item.get("appDisplayName", "unknown")

            return SSOEventRecord(
                user_id="",
                user_email=user_email,
                timestamp=ts,
                event_type=AuthEventType.LOGIN,
                app_name=app_name,
                ip_city=city,
                auth_method=item.get("clientAppUsed", "sso"),
                success=success,
                is_after_hours=self._is_after_hours(ts),
                is_weekend=ts.weekday() >= 5,
            )
        except Exception as e:
            logger.debug("Skipping Azure AD sign-in: %s", e)
            return None

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
            logger.error("Azure AD token error: %s", e)
            return None


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class SSOMetadataAnalyzer:
    """Extracts behavioral signals from SSO/IdP metadata.

    Works exclusively with login timestamps, app names, and session
    duration. Never sees credentials, tokens, or user content.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def analyze(
        self,
        events: List[SSOEventRecord],
        days: int = 14,
    ) -> SSOMetadataSignals:
        if not events:
            return self._empty_signals()

        successful = [e for e in events if e.success]
        if not successful:
            return self._empty_signals()

        # Group by day
        by_day: Dict[str, List[SSOEventRecord]] = defaultdict(list)
        for e in successful:
            by_day[e.timestamp.strftime("%Y-%m-%d")].append(e)

        # Login span per day
        daily_spans: List[float] = []
        first_logins: List[float] = []
        last_activities: List[float] = []

        for day_events in by_day.values():
            sorted_events = sorted(day_events, key=lambda e: e.timestamp)
            first = sorted_events[0].timestamp
            last = sorted_events[-1].timestamp
            span = (last - first).total_seconds() / 3600
            daily_spans.append(span)
            first_logins.append(first.hour + first.minute / 60)
            last_activities.append(last.hour + last.minute / 60)

        avg_span = sum(daily_spans) / len(daily_spans) if daily_spans else 0
        avg_first = sum(first_logins) / len(first_logins) if first_logins else 9
        avg_last = (
            sum(last_activities) / len(last_activities) if last_activities else 17
        )

        # Login span trend (compare first half vs second half)
        login_span_trend = 0.0
        if len(daily_spans) >= 4:
            mid = len(daily_spans) // 2
            first_half = sum(daily_spans[:mid]) / mid
            second_half = sum(daily_spans[mid:]) / (len(daily_spans) - mid)
            login_span_trend = second_half - first_half

        # App usage
        all_apps = set(e.app_name for e in successful)
        apps_per_day = len(all_apps) / max(len(by_day), 1)
        active_hours = len(set(e.timestamp.strftime("%Y-%m-%d-%H") for e in successful))
        app_switching = len(all_apps) / max(active_hours, 1)

        # Timing
        after_hours = [e for e in successful if e.is_after_hours]
        weekend = [e for e in successful if e.is_weekend]
        ah_ratio = len(after_hours) / max(len(successful), 1)
        wk_ratio = len(weekend) / max(len(successful), 1)

        # Peak hour
        hourly = [0] * 24
        for e in successful:
            hourly[e.timestamp.hour] += 1
        peak_hour = hourly.index(max(hourly))

        # Anomalies
        failed = [e for e in events if not e.success]
        failed_ratio = len(failed) / max(len(events), 1)
        cities = set(e.ip_city for e in successful if e.ip_city)

        # Composite scores
        overextension = self._session_overextension_score(
            avg_span, login_span_trend, avg_first, avg_last
        )
        boundary = self._boundary_erosion_score(ah_ratio, wk_ratio, avg_span)
        burnout, label = self._burnout_risk_score(
            overextension, boundary, app_switching, wk_ratio
        )

        daily = self._daily_breakdown(by_day)
        recs = self._generate_recommendations(
            avg_span, login_span_trend, ah_ratio, wk_ratio, app_switching, boundary
        )

        return SSOMetadataSignals(
            avg_login_span_hours=round(avg_span, 1),
            login_span_trend=round(login_span_trend, 2),
            avg_first_login_hour=round(avg_first, 1),
            avg_last_activity_hour=round(avg_last, 1),
            unique_apps_accessed=len(all_apps),
            avg_apps_per_day=round(apps_per_day, 1),
            app_switching_rate=round(app_switching, 2),
            after_hours_ratio=round(ah_ratio, 3),
            weekend_ratio=round(wk_ratio, 3),
            peak_login_hour=peak_hour,
            failed_login_ratio=round(failed_ratio, 3),
            location_changes=len(cities),
            session_overextension_score=round(overextension, 1),
            boundary_erosion_score=round(boundary, 1),
            burnout_risk_score=round(burnout, 1),
            risk_label=label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    def _session_overextension_score(
        self,
        avg_span: float,
        trend: float,
        avg_first: float,
        avg_last: float,
    ) -> float:
        """0-100: is the login window expanding dangerously?

        8-hour span is normal. 12+ is concerning. Expanding trend amplifies.
        """
        # Base: how far above 8 hours
        span_excess = max(0, avg_span - 8) / 8 * 60  # 16h = 60 points
        # Trend amplifier: expanding by 1h/week = +20
        trend_amp = max(0, trend) * 20
        # Early start penalty: before 7am average
        early_penalty = max(0, 7 - avg_first) * 5
        # Late finish penalty: after 20:00 average
        late_penalty = max(0, avg_last - 20) * 5

        return min(100, span_excess + trend_amp + early_penalty + late_penalty)

    def _boundary_erosion_score(
        self, ah_ratio: float, wk_ratio: float, avg_span: float
    ) -> float:
        """0-100: work-life boundary erosion from login patterns."""
        ah_component = min(100, ah_ratio * 250)
        wk_component = min(100, wk_ratio * 400)
        # Long sessions contribute to boundary erosion
        span_component = min(30, max(0, avg_span - 9) * 10)
        return ah_component * 0.40 + wk_component * 0.35 + span_component * 0.25

    def _burnout_risk_score(
        self,
        overextension: float,
        boundary: float,
        app_switching: float,
        wk_ratio: float,
    ) -> tuple:
        """Composite burnout risk from SSO patterns. Returns (score, label).

        Session overextension is the unique signal SSO provides — it captures
        actual working hours more accurately than any other data source.
        """
        # App switching over 5 apps/hour is cognitive overload
        switching_score = min(30, max(0, app_switching - 3) * 15)

        base = overextension * 0.40 + boundary * 0.35 + switching_score * 0.25

        # Interaction: overextension AND poor boundaries
        interaction = (overextension / 100) * (boundary / 100) * 20

        # Weekend login is strong predictor
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
        self, by_day: Dict[str, List[SSOEventRecord]]
    ) -> List[Dict[str, Any]]:
        result = []
        for day_str in sorted(by_day.keys()):
            events = sorted(by_day[day_str], key=lambda e: e.timestamp)
            first = events[0].timestamp
            last = events[-1].timestamp
            span = (last - first).total_seconds() / 3600

            result.append(
                {
                    "date": day_str,
                    "first_login": first.strftime("%H:%M"),
                    "last_activity": last.strftime("%H:%M"),
                    "login_span_hours": round(span, 1),
                    "total_logins": len(events),
                    "unique_apps": len(set(e.app_name for e in events)),
                    "after_hours_logins": sum(1 for e in events if e.is_after_hours),
                    "weekend_logins": sum(1 for e in events if e.is_weekend),
                    "failed_logins": sum(1 for e in events if not e.success),
                }
            )
        return result

    def _generate_recommendations(
        self,
        avg_span: float,
        trend: float,
        ah_ratio: float,
        wk_ratio: float,
        app_switching: float,
        boundary: float,
    ) -> List[str]:
        recs = []
        if avg_span > 12:
            recs.append(
                f"Average login span is {avg_span:.1f} hours — well above the healthy 8-hour range. "
                "Review workload distribution."
            )
        elif avg_span > 10:
            recs.append(
                f"Average login span is {avg_span:.1f} hours. "
                "Consider setting hard stop times."
            )
        if trend > 0.5:
            recs.append(
                f"Login span is expanding by {trend:.1f} hours week-over-week. "
                "This trajectory predicts burnout within 4-6 weeks."
            )
        if ah_ratio > 0.25:
            recs.append(
                f"{ah_ratio*100:.0f}% of logins are outside work hours. "
                "Configure SSO policies to flag after-hours access."
            )
        if wk_ratio > 0.10:
            recs.append(
                f"{wk_ratio*100:.0f}% of logins are on weekends. "
                "Weekend work is a strong burnout leading indicator."
            )
        if app_switching > 5:
            recs.append(
                f"High app switching rate ({app_switching:.1f} apps/hour). "
                "Consolidate tooling or batch context switches."
            )
        if boundary > 60:
            recs.append(
                "Boundary erosion is in the risk zone. "
                "Discuss workload expectations with leadership."
            )
        if not recs:
            recs.append("SSO patterns look healthy. Login hours are sustainable.")
        return recs

    def _empty_signals(self) -> SSOMetadataSignals:
        return SSOMetadataSignals(
            avg_login_span_hours=0,
            login_span_trend=0,
            avg_first_login_hour=9,
            avg_last_activity_hour=17,
            unique_apps_accessed=0,
            avg_apps_per_day=0,
            app_switching_rate=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            peak_login_hour=9,
            failed_login_ratio=0,
            location_changes=0,
            session_overextension_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No SSO data available. Connect your IdP to enable analysis."
            ],
        )


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class SSOMetadataRegistry:
    CONNECTOR_TYPES = {
        "okta": OktaSSOConnector,
        "azure_ad": AzureADSSOConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, SSOMetadataConnector] = {}

    def register(self, name: str, connector: SSOMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered SSO metadata connector: %s", name)

    def get(self, name: str) -> Optional[SSOMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


sso_metadata_registry = SSOMetadataRegistry()
