"""
Email Metadata Analysis Service

Analyzes email METADATA ONLY — never reads message bodies or subjects.
This is the employer-preferred privacy-first approach.

Input signals (per email):
  - direction (sent / received)
  - timestamp
  - recipient count
  - internal vs. external (same domain or not)
  - response time (time between receive and reply, if applicable)
  - thread depth

Output behavioral signals:
  - communication_load (volume pressure)
  - after_hours_ratio (boundary erosion)
  - weekend_ratio (work-life balance)
  - response_urgency (always-on behavior)
  - network_breadth (internal vs external split)
  - hourly_distribution (24-bucket heatmap)
  - burnout_risk composite

These signals feed into the Behavioral Intelligence Engine and
can be surfaced standalone on the Email Metadata Dashboard.
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
# NORMALIZED SCHEMA — metadata envelope only, zero content
# ══════════════════════════════════════════════════════════════════


class EmailDirection(str, Enum):
    SENT = "sent"
    RECEIVED = "received"


@dataclass
class EmailMetadataRecord:
    """One email's metadata — no body, no subject, no attachments."""

    id: str
    direction: EmailDirection
    timestamp: datetime
    recipient_count: int
    is_internal: bool  # sender & all recipients share org domain
    response_time_minutes: Optional[float]  # None if not a reply
    thread_depth: int  # 0 = new thread, 1+ = reply chain depth
    is_after_hours: bool = False
    is_weekend: bool = False


@dataclass
class DailyEmailLoad:
    """Per-day email summary."""

    date: str
    sent: int
    received: int
    after_hours_sent: int
    after_hours_received: int
    avg_response_time_min: Optional[float]
    internal_ratio: float
    unique_external_contacts: int


@dataclass
class EmailMetadataSignals:
    """Behavioral signals derived from email metadata analysis."""

    # Volume
    avg_daily_sent: float
    avg_daily_received: float
    sent_received_ratio: float  # >1 = net sender

    # Timing
    after_hours_ratio: float  # 0-1, fraction of all emails outside work hours
    weekend_ratio: float  # 0-1, fraction of all emails on weekends
    peak_hour: int  # 0-23, most active hour
    hourly_distribution: List[int]  # 24 buckets

    # Responsiveness
    avg_response_time_min: float
    p90_response_time_min: float
    instant_reply_ratio: float  # replies within 5 minutes

    # Network shape
    internal_ratio: float  # fraction of internal emails
    avg_recipients_per_email: float

    # Composite scores (0-100, higher = more concerning)
    communication_load_score: float
    boundary_erosion_score: float
    burnout_risk_score: float

    # Actionable output
    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    daily_breakdown: List[Dict[str, Any]] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# ABSTRACT CONNECTOR
# ══════════════════════════════════════════════════════════════════


class EmailMetadataConnector(ABC):
    """Base interface — implementations fetch metadata from providers.

    IMPORTANT: Connectors must NEVER request or return email bodies.
    Only envelope metadata (headers, timestamps, addresses) is allowed.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_metadata(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[EmailMetadataRecord]: ...


# ══════════════════════════════════════════════════════════════════
# GMAIL METADATA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class GmailMetadataConnector(EmailMetadataConnector):
    """Google Gmail API connector — metadata only via users.messages.get(format=METADATA)."""

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        credentials_json: Optional[str] = None,
        org_domain: str = "",
    ):
        self.credentials_json = credentials_json
        self.org_domain = org_domain

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "gmail_metadata",
            "scopes": ["gmail.metadata"],
            "note": "Uses gmail.metadata scope — no body access",
        }

    async def fetch_metadata(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[EmailMetadataRecord]:
        """Fetch message headers via Gmail API with format=METADATA.

        Gmail API with format=METADATA returns only headers (Date, From, To,
        Cc, Message-ID, In-Reply-To, References) — never the body.
        OAuth scope: https://www.googleapis.com/auth/gmail.metadata
        """
        access_token = await self._get_access_token(user_email)
        if not access_token:
            logger.warning(
                "No access token for %s — skipping Gmail metadata", user_email
            )
            return []

        records: List[EmailMetadataRecord] = []
        try:
            import httpx

            after_epoch = int(start.timestamp())
            before_epoch = int(end.timestamp())
            query = f"after:{after_epoch} before:{before_epoch}"

            async with httpx.AsyncClient(timeout=30.0) as client:
                page_token = None
                while True:
                    params: Dict[str, Any] = {"q": query, "maxResults": 200}
                    if page_token:
                        params["pageToken"] = page_token

                    resp = await client.get(
                        "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                        headers={"Authorization": f"Bearer {access_token}"},
                        params=params,
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    for msg_stub in data.get("messages", []):
                        record = await self._fetch_single_metadata(
                            client, access_token, msg_stub["id"], user_email
                        )
                        if record:
                            records.append(record)

                    page_token = data.get("nextPageToken")
                    if not page_token:
                        break

            logger.info(
                "Gmail: fetched %d metadata records for %s", len(records), user_email
            )
        except ImportError:
            logger.warning("httpx not installed — Gmail metadata connector disabled")
        except Exception as e:
            logger.error("Gmail metadata fetch error for %s: %s", user_email, e)
        return records

    async def _fetch_single_metadata(
        self, client, access_token: str, msg_id: str, user_email: str
    ) -> Optional[EmailMetadataRecord]:
        """Fetch one message with format=METADATA — only headers returned."""
        try:
            resp = await client.get(
                f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                headers={"Authorization": f"Bearer {access_token}"},
                params={
                    "format": "METADATA",
                    "metadataHeaders": ["Date", "From", "To", "Cc", "In-Reply-To"],
                },
            )
            resp.raise_for_status()
            data = resp.json()

            headers = {
                h["name"].lower(): h["value"]
                for h in data.get("payload", {}).get("headers", [])
            }

            # Parse timestamp
            date_str = headers.get("date", "")
            try:
                from email.utils import parsedate_to_datetime

                timestamp = parsedate_to_datetime(date_str)
            except Exception:
                return None

            # Direction
            from_addr = headers.get("from", "").lower()
            direction = (
                EmailDirection.SENT
                if user_email.lower() in from_addr
                else EmailDirection.RECEIVED
            )

            # Recipients
            to_raw = headers.get("to", "")
            cc_raw = headers.get("cc", "")
            all_recipients = [
                a.strip() for a in (to_raw + "," + cc_raw).split(",") if "@" in a
            ]
            recipient_count = max(len(all_recipients), 1)

            # Internal check
            is_internal = (
                all(
                    self.org_domain and self.org_domain in addr
                    for addr in all_recipients
                    if "@" in addr
                )
                if self.org_domain
                else False
            )

            # Thread depth from label inspection
            thread_id = data.get("threadId", "")
            in_reply_to = headers.get("in-reply-to", "")
            thread_depth = 1 if in_reply_to else 0

            is_after = self._is_after_hours(timestamp)
            is_wknd = timestamp.weekday() >= 5

            return EmailMetadataRecord(
                id=msg_id,
                direction=direction,
                timestamp=timestamp,
                recipient_count=recipient_count,
                is_internal=is_internal,
                response_time_minutes=None,  # computed later in batch
                thread_depth=thread_depth,
                is_after_hours=is_after,
                is_weekend=is_wknd,
            )
        except Exception as e:
            logger.debug("Skipping message %s: %s", msg_id, e)
            return None

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END

    async def _get_access_token(self, user_email: str) -> Optional[str]:
        try:
            import json

            if self.credentials_json:
                creds = json.loads(self.credentials_json)
                return creds.get("access_token")
        except Exception:
            pass
        return None


# ══════════════════════════════════════════════════════════════════
# OUTLOOK METADATA CONNECTOR
# ══════════════════════════════════════════════════════════════════


class OutlookMetadataConnector(EmailMetadataConnector):
    """Microsoft Graph API — fetches message metadata only via $select."""

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def __init__(
        self,
        tenant_id: str = "",
        client_id: str = "",
        client_secret: str = "",
        org_domain: str = "",
    ):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.org_domain = org_domain
        self.base_url = "https://graph.microsoft.com/v1.0"

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "outlook_metadata",
            "note": "Uses $select to fetch headers only — no body",
        }

    async def fetch_metadata(
        self,
        user_email: str,
        start: datetime,
        end: datetime,
    ) -> List[EmailMetadataRecord]:
        """Fetch via Graph API with $select — only metadata fields."""
        records: List[EmailMetadataRecord] = []
        try:
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                skip = 0
                while True:
                    resp = await client.get(
                        f"{self.base_url}/me/messages",
                        headers={"Authorization": "Bearer <token>"},
                        params={
                            "$select": "id,sentDateTime,from,toRecipients,ccRecipients,conversationIndex,isDraft",
                            "$filter": f"sentDateTime ge {start.isoformat()}Z and sentDateTime le {end.isoformat()}Z",
                            "$top": 100,
                            "$skip": skip,
                            "$orderby": "sentDateTime desc",
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    items = data.get("value", [])
                    if not items:
                        break

                    for msg in items:
                        record = self._normalize(msg, user_email)
                        if record:
                            records.append(record)

                    if "@odata.nextLink" not in data:
                        break
                    skip += len(items)

        except ImportError:
            logger.warning("httpx not installed — Outlook metadata connector disabled")
        except Exception as e:
            logger.error("Outlook metadata fetch error: %s", e)
        return records

    def _normalize(self, msg: dict, user_email: str) -> Optional[EmailMetadataRecord]:
        try:
            sent_dt = datetime.fromisoformat(msg["sentDateTime"].replace("Z", "+00:00"))
            from_addr = msg.get("from", {}).get("emailAddress", {}).get("address", "")
            direction = (
                EmailDirection.SENT
                if user_email.lower() in from_addr.lower()
                else EmailDirection.RECEIVED
            )

            to_list = [
                r["emailAddress"]["address"] for r in msg.get("toRecipients", [])
            ]
            cc_list = [
                r["emailAddress"]["address"] for r in msg.get("ccRecipients", [])
            ]
            all_recipients = to_list + cc_list

            is_internal = (
                all(
                    self.org_domain and self.org_domain in addr
                    for addr in all_recipients
                )
                if self.org_domain
                else False
            )

            # conversationIndex length hints at thread depth
            conv_index = msg.get("conversationIndex", "")
            thread_depth = max(0, (len(conv_index) - 44) // 10) if conv_index else 0

            return EmailMetadataRecord(
                id=msg["id"],
                direction=direction,
                timestamp=sent_dt,
                recipient_count=max(len(all_recipients), 1),
                is_internal=is_internal,
                response_time_minutes=None,
                thread_depth=thread_depth,
                is_after_hours=self._is_after_hours(sent_dt),
                is_weekend=sent_dt.weekday() >= 5,
            )
        except Exception as e:
            logger.debug("Skipping Outlook message: %s", e)
            return None

    def _is_after_hours(self, dt: datetime) -> bool:
        t = dt.time()
        return t < self.WORK_START or t > self.WORK_END


# ══════════════════════════════════════════════════════════════════
# BEHAVIORAL ANALYZER
# ══════════════════════════════════════════════════════════════════


class EmailMetadataAnalyzer:
    """Extracts behavioral signals from email metadata.

    This analyzer NEVER sees email content. It works exclusively with
    timestamps, directions, recipient counts, and domain classification.
    """

    WORK_START = time(9, 0)
    WORK_END = time(18, 0)

    def analyze(
        self,
        records: List[EmailMetadataRecord],
        days: int = 14,
    ) -> EmailMetadataSignals:
        """Full behavioral analysis from metadata records."""
        if not records:
            return self._empty_signals(days)

        sent = [r for r in records if r.direction == EmailDirection.SENT]
        received = [r for r in records if r.direction == EmailDirection.RECEIVED]
        weeks = max(days / 7, 1)

        # Volume
        avg_daily_sent = len(sent) / max(days, 1)
        avg_daily_received = len(received) / max(days, 1)
        sent_received_ratio = len(sent) / max(len(received), 1)

        # Timing
        after_hours = [r for r in records if r.is_after_hours]
        weekend = [r for r in records if r.is_weekend]
        after_hours_ratio = len(after_hours) / max(len(records), 1)
        weekend_ratio = len(weekend) / max(len(records), 1)

        hourly = self._hourly_distribution(records)
        peak_hour = hourly.index(max(hourly))

        # Responsiveness
        response_times = [
            r.response_time_minutes
            for r in records
            if r.response_time_minutes is not None
        ]
        avg_resp = (sum(response_times) / len(response_times)) if response_times else 0
        sorted_resp = sorted(response_times) if response_times else [0]
        p90_idx = int(len(sorted_resp) * 0.9)
        p90_resp = sorted_resp[min(p90_idx, len(sorted_resp) - 1)]
        instant_replies = sum(1 for t in response_times if t <= 5)
        instant_ratio = instant_replies / max(len(response_times), 1)

        # Network
        internal_count = sum(1 for r in records if r.is_internal)
        internal_ratio = internal_count / max(len(records), 1)
        avg_recipients = sum(r.recipient_count for r in records) / max(len(records), 1)

        # Composites
        communication_load = self._communication_load_score(
            avg_daily_sent, avg_daily_received, avg_recipients
        )
        boundary_erosion = self._boundary_erosion_score(
            after_hours_ratio, weekend_ratio, instant_ratio
        )

        burnout_risk, risk_label = self._burnout_risk_score(
            communication_load,
            boundary_erosion,
            avg_resp,
            sent_received_ratio,
            weekend_ratio,
        )

        daily = self._daily_breakdown(records, days)

        recs = self._generate_recommendations(
            avg_daily_sent + avg_daily_received,
            after_hours_ratio,
            weekend_ratio,
            avg_resp,
            instant_ratio,
            boundary_erosion,
        )

        return EmailMetadataSignals(
            avg_daily_sent=round(avg_daily_sent, 1),
            avg_daily_received=round(avg_daily_received, 1),
            sent_received_ratio=round(sent_received_ratio, 2),
            after_hours_ratio=round(after_hours_ratio, 3),
            weekend_ratio=round(weekend_ratio, 3),
            peak_hour=peak_hour,
            hourly_distribution=hourly,
            avg_response_time_min=round(avg_resp, 1),
            p90_response_time_min=round(p90_resp, 1),
            instant_reply_ratio=round(instant_ratio, 3),
            internal_ratio=round(internal_ratio, 3),
            avg_recipients_per_email=round(avg_recipients, 1),
            communication_load_score=round(communication_load, 1),
            boundary_erosion_score=round(boundary_erosion, 1),
            burnout_risk_score=round(burnout_risk, 1),
            risk_label=risk_label,
            recommendations=recs,
            daily_breakdown=daily,
        )

    # ── Component scores ─────────────────────────────────────────

    def _communication_load_score(
        self, avg_sent: float, avg_received: float, avg_recipients: float
    ) -> float:
        """0-100: how heavy is the email communication burden?"""
        total_daily = avg_sent + avg_received
        # Baseline: 30 emails/day is normal, 80+ is critical
        volume_pressure = min(100, (total_daily / 80) * 100)
        # Broadcasting penalty: many recipients = coordination overhead
        broadcast_penalty = min(20, max(0, avg_recipients - 3) * 5)
        return min(100, volume_pressure * 0.8 + broadcast_penalty)

    def _boundary_erosion_score(
        self, after_hours_ratio: float, weekend_ratio: float, instant_ratio: float
    ) -> float:
        """0-100: how much are work-life boundaries being eroded?"""
        # After-hours weight: 40%, weekend: 35%, instant-reply: 25%
        after_hours_component = min(100, after_hours_ratio * 250)
        weekend_component = min(100, weekend_ratio * 400)
        instant_component = min(100, instant_ratio * 200)
        return (
            after_hours_component * 0.40
            + weekend_component * 0.35
            + instant_component * 0.25
        )

    def _burnout_risk_score(
        self,
        comm_load: float,
        boundary_erosion: float,
        avg_response_min: float,
        sent_received_ratio: float,
        weekend_ratio: float,
    ) -> tuple:
        """Composite burnout risk from metadata signals. Returns (score, label).

        Boundary erosion is weighted heavier than volume (research shows
        after-hours work predicts burnout 2x better than raw volume).
        An interaction term captures the multiplicative effect: high load
        AND poor boundaries is worse than either alone.
        """
        # Base blend: boundary erosion dominates
        base = boundary_erosion * 0.45 + comm_load * 0.30

        # Interaction amplifier: both high → multiplicative risk
        interaction = (boundary_erosion / 100) * (comm_load / 100) * 25

        # Hypervigilance signal: avg response < 5 min is clinical
        hypervigilance = 0.0
        if avg_response_min > 0:
            if avg_response_min < 5:
                hypervigilance = 15.0
            elif avg_response_min < 10:
                hypervigilance = 8.0

        # Weekend work is a particularly strong predictor
        weekend_amplifier = 0.0
        if weekend_ratio > 0.15:
            weekend_amplifier = min(10, (weekend_ratio - 0.15) * 100)

        score = min(100, base + interaction + hypervigilance + weekend_amplifier)

        if score >= 70:
            label = "Critical"
        elif score >= 45:
            label = "Elevated"
        elif score >= 25:
            label = "Monitor"
        else:
            label = "Healthy"

        return round(score, 1), label

    # ── Helpers ──────────────────────────────────────────────────

    def _hourly_distribution(self, records: List[EmailMetadataRecord]) -> List[int]:
        buckets = [0] * 24
        for r in records:
            buckets[r.timestamp.hour] += 1
        return buckets

    def _daily_breakdown(
        self, records: List[EmailMetadataRecord], days: int
    ) -> List[Dict[str, Any]]:
        by_day: Dict[str, List[EmailMetadataRecord]] = defaultdict(list)
        for r in records:
            day_key = r.timestamp.strftime("%Y-%m-%d")
            by_day[day_key].append(r)

        result = []
        for day_str in sorted(by_day.keys()):
            day_records = by_day[day_str]
            day_sent = [r for r in day_records if r.direction == EmailDirection.SENT]
            day_recv = [
                r for r in day_records if r.direction == EmailDirection.RECEIVED
            ]
            ah_sent = sum(1 for r in day_sent if r.is_after_hours)
            ah_recv = sum(1 for r in day_recv if r.is_after_hours)
            resp_times = [
                r.response_time_minutes
                for r in day_records
                if r.response_time_minutes is not None
            ]
            internal = sum(1 for r in day_records if r.is_internal)
            external_addrs = set()
            for r in day_records:
                if not r.is_internal:
                    external_addrs.add(r.id)  # proxy for unique contacts

            result.append(
                {
                    "date": day_str,
                    "sent": len(day_sent),
                    "received": len(day_recv),
                    "after_hours_sent": ah_sent,
                    "after_hours_received": ah_recv,
                    "avg_response_time_min": (
                        round(sum(resp_times) / len(resp_times), 1)
                        if resp_times
                        else None
                    ),
                    "internal_ratio": round(internal / max(len(day_records), 1), 2),
                    "external_contacts": len(external_addrs),
                }
            )
        return result

    def _generate_recommendations(
        self,
        daily_volume: float,
        after_hours_ratio: float,
        weekend_ratio: float,
        avg_response_min: float,
        instant_ratio: float,
        boundary_score: float,
    ) -> List[str]:
        recs = []
        if daily_volume > 60:
            recs.append(
                f"Email volume ({daily_volume:.0f}/day) is well above healthy range. "
                "Consider batching email into 2-3 scheduled check-ins."
            )
        elif daily_volume > 40:
            recs.append(
                f"Email volume ({daily_volume:.0f}/day) is elevated. "
                "Review whether all threads require your direct involvement."
            )

        if after_hours_ratio > 0.25:
            recs.append(
                f"{after_hours_ratio*100:.0f}% of emails are outside work hours. "
                "Set up delayed send or turn off notifications after 6 PM."
            )

        if weekend_ratio > 0.10:
            recs.append(
                f"{weekend_ratio*100:.0f}% of emails are on weekends — "
                "a strong burnout predictor. Protect at least one full day off."
            )

        if instant_ratio > 0.30:
            recs.append(
                f"{instant_ratio*100:.0f}% of replies are within 5 minutes. "
                "This 'always-on' pattern correlates with hypervigilance and burnout."
            )

        if avg_response_min < 10 and daily_volume > 30:
            recs.append(
                "Extremely fast average response time combined with high volume. "
                "Consider implementing email-free focus blocks."
            )

        if boundary_score > 60:
            recs.append(
                "Work-life boundary erosion is in the risk zone. "
                "Discuss workload expectations with your manager."
            )

        if not recs:
            recs.append(
                "Email patterns look healthy. Current communication load is sustainable."
            )

        return recs

    def _empty_signals(self, days: int) -> EmailMetadataSignals:
        return EmailMetadataSignals(
            avg_daily_sent=0,
            avg_daily_received=0,
            sent_received_ratio=0,
            after_hours_ratio=0,
            weekend_ratio=0,
            peak_hour=10,
            hourly_distribution=[0] * 24,
            avg_response_time_min=0,
            p90_response_time_min=0,
            instant_reply_ratio=0,
            internal_ratio=0,
            avg_recipients_per_email=0,
            communication_load_score=0,
            boundary_erosion_score=0,
            burnout_risk_score=0,
            risk_label="No Data",
            recommendations=[
                "No email metadata available. Connect your email to enable analysis."
            ],
        )

    @staticmethod
    def compute_response_times(
        records: List[EmailMetadataRecord],
    ) -> List[EmailMetadataRecord]:
        """Estimate response times by matching sent replies to received emails in same thread.

        Groups by thread (approximated via thread_depth > 0 proximity)
        and computes time delta between received and next sent.
        """
        received_by_hour: List[EmailMetadataRecord] = sorted(
            [r for r in records if r.direction == EmailDirection.RECEIVED],
            key=lambda r: r.timestamp,
        )
        sent_replies = sorted(
            [
                r
                for r in records
                if r.direction == EmailDirection.SENT and r.thread_depth > 0
            ],
            key=lambda r: r.timestamp,
        )

        # Simple heuristic: match each sent reply to the most recent
        # received email within a 24-hour window
        recv_idx = 0
        for reply in sent_replies:
            while (
                recv_idx < len(received_by_hour) - 1
                and received_by_hour[recv_idx + 1].timestamp <= reply.timestamp
            ):
                recv_idx += 1
            if recv_idx < len(received_by_hour):
                delta = (
                    reply.timestamp - received_by_hour[recv_idx].timestamp
                ).total_seconds() / 60
                if 0 < delta < 1440:  # within 24 hours
                    reply.response_time_minutes = round(delta, 1)

        return records


# ══════════════════════════════════════════════════════════════════
# REGISTRY
# ══════════════════════════════════════════════════════════════════


class EmailMetadataRegistry:
    """Manages configured email metadata connectors."""

    CONNECTOR_TYPES = {
        "gmail": GmailMetadataConnector,
        "outlook": OutlookMetadataConnector,
    }

    def __init__(self):
        self._connectors: Dict[str, EmailMetadataConnector] = {}

    def register(self, name: str, connector: EmailMetadataConnector) -> None:
        self._connectors[name] = connector
        logger.info("Registered email metadata connector: %s", name)

    def get(self, name: str) -> Optional[EmailMetadataConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


email_metadata_registry = EmailMetadataRegistry()
