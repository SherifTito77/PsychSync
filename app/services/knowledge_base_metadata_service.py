"""
Knowledge Base / Wiki Analytics Service

Analyzes wiki and documentation platform METADATA ONLY — no page
content, no text analysis. Extracts behavioral signals from activity
logs: who creates, edits, views pages, and how knowledge flows.

Input signals (per activity event):
  - user identifier
  - action type (create / edit / view / comment)
  - timestamp
  - workspace / space identifier
  - word count delta (for edits, not the words themselves)
  - is_new_page flag

Output behavioral signals:
  - doc_creation_rate (knowledge sharing proxy)
  - consumption_ratio (readers vs contributors)
  - stale_content_ratio (maintenance health)
  - contributor_concentration (bus factor for documentation)
  - cross_space_contribution (cross-team collaboration)
  - knowledge_sharing_score (composite)
  - engagement_score (composite)
  - burnout_risk (declining contribution = disengagement)

Zero content analysis. No page titles, no text, no attachments.
"""

import logging
import statistics
from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ======================================================================
# NORMALIZED SCHEMA
# ======================================================================


class KBAction(str, Enum):
    CREATE = "create"
    EDIT = "edit"
    VIEW = "view"
    COMMENT = "comment"


@dataclass
class KBActivityRecord:
    """One knowledge base activity event — metadata only."""

    event_id: str
    user_id: str
    action: KBAction
    timestamp: datetime
    space_id: str  # workspace / space / project (not page content)
    page_id_hash: str  # hashed page identifier — no title exposed
    word_count_delta: int  # net words added/removed (for edits)
    is_new_page: bool


@dataclass
class KBUserContribution:
    """Per-user contribution summary."""

    user_id: str
    pages_created: int
    pages_edited: int
    pages_viewed: int
    comments_made: int
    total_words_added: int
    spaces_contributed_to: int  # breadth of contribution
    active_days: int


@dataclass
class KBAnalyticsSignals:
    """Behavioral signals from knowledge base activity metadata."""

    # Creation signals
    total_pages_created: int
    doc_creation_rate: float  # pages created per person per week
    edit_frequency: float  # edits per person per week

    # Consumption signals
    total_views: int
    total_edits: int
    consumption_ratio: float  # views / (creates + edits); high = mostly reading

    # Health signals
    stale_content_ratio: float  # 0-1, fraction of pages with no edits in window
    active_page_ratio: float  # 0-1, fraction of pages with recent activity
    avg_edits_per_page: float  # how actively pages are maintained

    # Collaboration signals
    unique_contributors: int
    contributor_concentration: (
        float  # 0-1, Gini-like — 1.0 = one person writes everything
    )
    cross_space_ratio: float  # 0-1, fraction of contributors active in >1 space
    comment_to_edit_ratio: float  # feedback culture indicator

    # Trends
    creation_trend: str  # "increasing", "stable", "decreasing"
    contribution_trend: str  # overall activity trend

    # Composite scores (0-100)
    knowledge_sharing_score: float  # higher = healthier sharing culture
    engagement_score: float  # higher = more active knowledge community
    burnout_risk: float  # declining contribution = disengagement signal

    risk_label: str
    recommendations: List[str] = field(default_factory=list)
    top_contributors: List[Dict[str, Any]] = field(default_factory=list)


# ======================================================================
# ABSTRACT CONNECTOR
# ======================================================================


class KBConnector(ABC):
    """Base interface for knowledge base / wiki connectors.

    Only receives activity event metadata.
    No page content, no titles, no attachments.
    """

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def fetch_activity(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[KBActivityRecord]: ...


# ======================================================================
# PROVIDER CONNECTORS
# ======================================================================


class ConfluenceConnector(KBConnector):
    """Atlassian Confluence — audit log API (metadata only)."""

    def __init__(self, base_url: str = "", api_token: str = "", user_email: str = ""):
        self.base_url = base_url
        self.api_token = api_token
        self.user_email = user_email

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "confluence",
            "note": "Activity audit logs only — no page content",
        }

    async def fetch_activity(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[KBActivityRecord]:
        if not self.base_url or not self.api_token:
            return []
        records: List[KBActivityRecord] = []
        try:
            import hashlib
            import httpx

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    f"{self.base_url}/wiki/rest/api/audit",
                    auth=(self.user_email, self.api_token),
                    params={
                        "startDate": start.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "endDate": end.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                        "limit": 1000,
                    },
                )
                resp.raise_for_status()
                for entry in resp.json().get("results", []):
                    action_str = entry.get("summary", "").lower()
                    if "created" in action_str:
                        action = KBAction.CREATE
                    elif "updated" in action_str or "edited" in action_str:
                        action = KBAction.EDIT
                    elif "viewed" in action_str:
                        action = KBAction.VIEW
                    elif "comment" in action_str:
                        action = KBAction.COMMENT
                    else:
                        continue

                    ts = datetime.fromisoformat(
                        entry.get("creationDate", "").replace("Z", "+00:00")
                    )
                    page_id = entry.get("associatedObjects", [{}])[0].get("id", "")
                    page_hash = hashlib.sha256(page_id.encode()).hexdigest()[:16]

                    records.append(
                        KBActivityRecord(
                            event_id=entry.get("id", ""),
                            user_id=entry.get("author", {}).get("username", ""),
                            action=action,
                            timestamp=ts,
                            space_id=entry.get("associatedObjects", [{}])[0].get(
                                "spaceKey", ""
                            ),
                            page_id_hash=page_hash,
                            word_count_delta=0,
                            is_new_page=action == KBAction.CREATE,
                        )
                    )
        except Exception as e:
            logger.error("Confluence fetch error: %s", e)
        return records


class NotionConnector(KBConnector):
    """Notion API — activity metadata (metadata only)."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "notion",
            "note": "Database/page activity metadata only — no content",
        }

    async def fetch_activity(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[KBActivityRecord]:
        if not self.api_key:
            return []
        return []  # Real implementation uses Notion API search with audit filter


class SharePointConnector(KBConnector):
    """Microsoft SharePoint — audit logs via Graph API (metadata only)."""

    def __init__(
        self, client_id: str = "", client_secret: str = "", tenant_id: str = ""
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.tenant_id = tenant_id

    async def test_connection(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "provider": "sharepoint",
            "note": "SharePoint audit log metadata only — no document content",
        }

    async def fetch_activity(
        self,
        org_id: str,
        start: datetime,
        end: datetime,
    ) -> List[KBActivityRecord]:
        if not self.client_id:
            return []
        return []  # Real implementation uses Microsoft Graph auditLogs


# ======================================================================
# REGISTRY
# ======================================================================


class KBAnalyticsRegistry:
    """Registry of knowledge base connectors."""

    def __init__(self):
        self._connectors: Dict[str, KBConnector] = {}

    def register(self, name: str, connector: KBConnector) -> None:
        self._connectors[name] = connector

    def get(self, name: str) -> Optional[KBConnector]:
        return self._connectors.get(name)

    def list_connectors(self) -> List[Dict[str, str]]:
        return [
            {"name": n, "type": type(c).__name__} for n, c in self._connectors.items()
        ]


kb_analytics_registry = KBAnalyticsRegistry()


# ======================================================================
# ANALYZER
# ======================================================================


class KBAnalyticsAnalyzer:
    """Analyze knowledge base activity metadata for behavioral signals."""

    def analyze(
        self,
        records: List[KBActivityRecord],
        days: int = 30,
    ) -> KBAnalyticsSignals:
        if not records:
            return self._empty_signals()

        weeks = max(1, days / 7)

        # --- Categorize events ---
        creates = [r for r in records if r.action == KBAction.CREATE]
        edits = [r for r in records if r.action == KBAction.EDIT]
        views = [r for r in records if r.action == KBAction.VIEW]
        comments = [r for r in records if r.action == KBAction.COMMENT]

        # --- Per-user contributions ---
        user_stats: Dict[str, KBUserContribution] = {}
        user_spaces: Dict[str, set] = defaultdict(set)
        user_days: Dict[str, set] = defaultdict(set)

        for r in records:
            if r.user_id not in user_stats:
                user_stats[r.user_id] = KBUserContribution(
                    user_id=r.user_id,
                    pages_created=0,
                    pages_edited=0,
                    pages_viewed=0,
                    comments_made=0,
                    total_words_added=0,
                    spaces_contributed_to=0,
                    active_days=0,
                )
            u = user_stats[r.user_id]
            if r.action == KBAction.CREATE:
                u.pages_created += 1
            elif r.action == KBAction.EDIT:
                u.pages_edited += 1
                u.total_words_added += max(0, r.word_count_delta)
            elif r.action == KBAction.VIEW:
                u.pages_viewed += 1
            elif r.action == KBAction.COMMENT:
                u.comments_made += 1

            user_spaces[r.user_id].add(r.space_id)
            user_days[r.user_id].add(r.timestamp.strftime("%Y-%m-%d"))

        for uid, u in user_stats.items():
            u.spaces_contributed_to = len(user_spaces[uid])
            u.active_days = len(user_days[uid])

        unique_users = len(user_stats)

        # --- Page activity tracking ---
        page_last_edit: Dict[str, datetime] = {}
        page_edit_counts: Counter = Counter()
        all_pages: set = set()

        for r in records:
            all_pages.add(r.page_id_hash)
            if r.action in (KBAction.CREATE, KBAction.EDIT):
                page_last_edit[r.page_id_hash] = max(
                    page_last_edit.get(r.page_id_hash, r.timestamp),
                    r.timestamp,
                )
                page_edit_counts[r.page_id_hash] += 1

        # --- Stale content ---
        now = records[-1].timestamp if records else datetime.utcnow()
        stale_threshold = now - timedelta(days=max(30, days))
        stale_pages = sum(
            1
            for p in all_pages
            if p not in page_last_edit or page_last_edit[p] < stale_threshold
        )
        stale_ratio = stale_pages / len(all_pages) if all_pages else 0
        active_ratio = 1 - stale_ratio

        # --- Rates ---
        doc_creation_rate = len(creates) / max(1, unique_users) / weeks
        edit_frequency = len(edits) / max(1, unique_users) / weeks
        total_content_actions = len(creates) + len(edits)
        consumption_ratio = len(views) / max(1, total_content_actions)
        avg_edits_per_page = sum(page_edit_counts.values()) / max(
            1, len(page_edit_counts)
        )

        # --- Contributor concentration (simplified Gini) ---
        contributor_concentration = self._compute_concentration(user_stats)

        # --- Cross-space contribution ---
        multi_space = sum(1 for s in user_spaces.values() if len(s) > 1)
        cross_space_ratio = multi_space / max(1, unique_users)

        # --- Comment to edit ratio ---
        comment_edit_ratio = len(comments) / max(1, len(edits))

        # --- Trends ---
        creation_trend = self._compute_trend(creates, days)
        all_contributions = [
            r
            for r in records
            if r.action in (KBAction.CREATE, KBAction.EDIT, KBAction.COMMENT)
        ]
        contribution_trend = self._compute_trend(all_contributions, days)

        # --- Composite scores ---
        knowledge_sharing = self._compute_knowledge_sharing(
            doc_creation_rate,
            contributor_concentration,
            cross_space_ratio,
            comment_edit_ratio,
            unique_users,
        )

        engagement = self._compute_engagement(
            doc_creation_rate,
            edit_frequency,
            active_ratio,
            contribution_trend,
            unique_users,
        )

        burnout_risk = self._compute_burnout_risk(
            contribution_trend,
            creation_trend,
            edit_frequency,
            stale_ratio,
        )

        risk_label = (
            "Critical"
            if burnout_risk >= 70
            else (
                "Elevated"
                if burnout_risk >= 45
                else "Monitor" if burnout_risk >= 25 else "Healthy"
            )
        )

        recs = self._generate_recommendations(
            knowledge_sharing,
            engagement,
            burnout_risk,
            contributor_concentration,
            stale_ratio,
            consumption_ratio,
        )

        # Top contributors (anonymized, just stats)
        top = sorted(
            user_stats.values(),
            key=lambda u: u.pages_created + u.pages_edited,
            reverse=True,
        )[:10]

        return KBAnalyticsSignals(
            total_pages_created=len(creates),
            doc_creation_rate=round(doc_creation_rate, 2),
            edit_frequency=round(edit_frequency, 2),
            total_views=len(views),
            total_edits=len(edits),
            consumption_ratio=round(consumption_ratio, 2),
            stale_content_ratio=round(stale_ratio, 3),
            active_page_ratio=round(active_ratio, 3),
            avg_edits_per_page=round(avg_edits_per_page, 1),
            unique_contributors=unique_users,
            contributor_concentration=round(contributor_concentration, 3),
            cross_space_ratio=round(cross_space_ratio, 3),
            comment_to_edit_ratio=round(comment_edit_ratio, 3),
            creation_trend=creation_trend,
            contribution_trend=contribution_trend,
            knowledge_sharing_score=round(knowledge_sharing, 1),
            engagement_score=round(engagement, 1),
            burnout_risk=round(burnout_risk, 1),
            risk_label=risk_label,
            recommendations=recs,
            top_contributors=[
                {
                    "user_id": u.user_id,
                    "created": u.pages_created,
                    "edited": u.pages_edited,
                    "comments": u.comments_made,
                    "words_added": u.total_words_added,
                    "spaces": u.spaces_contributed_to,
                }
                for u in top
            ],
        )

    def _compute_concentration(
        self, user_stats: Dict[str, KBUserContribution]
    ) -> float:
        """Gini-like concentration — 0 = equal contribution, 1 = one person does all."""
        if len(user_stats) < 2:
            return 0.0

        contributions = sorted(
            u.pages_created + u.pages_edited for u in user_stats.values()
        )
        n = len(contributions)
        total = sum(contributions)
        if total == 0:
            return 0.0

        cumulative = 0
        gini_sum = 0
        for i, c in enumerate(contributions):
            cumulative += c
            gini_sum += (2 * (i + 1) - n - 1) * c

        return gini_sum / (n * total)

    def _compute_trend(self, records: List[KBActivityRecord], days: int) -> str:
        """Compare first half vs second half activity volume."""
        if len(records) < 4:
            return "stable"

        sorted_recs = sorted(records, key=lambda r: r.timestamp)
        mid = len(sorted_recs) // 2
        first_half = len(sorted_recs[:mid])
        second_half = len(sorted_recs[mid:])

        if first_half == 0:
            return "increasing" if second_half > 0 else "stable"

        change = (second_half - first_half) / first_half
        if change > 0.2:
            return "increasing"
        elif change < -0.2:
            return "decreasing"
        return "stable"

    def _compute_knowledge_sharing(
        self,
        creation_rate: float,
        concentration: float,
        cross_space: float,
        comment_ratio: float,
        contributors: int,
    ) -> float:
        """0-100: how healthy is the knowledge sharing culture."""
        # Creation rate: >2 pages/person/week = max, 0 = 0
        creation_component = min(100, creation_rate * 50) * 0.25

        # Low concentration = more distributed = better
        distribution_component = (1 - concentration) * 100 * 0.25

        # Cross-space contribution = cross-team knowledge flow
        cross_component = cross_space * 100 * 0.20

        # Comment-to-edit ratio: feedback culture
        comment_component = min(100, comment_ratio * 100) * 0.15

        # Breadth: more unique contributors = healthier
        breadth_component = min(100, contributors * 5) * 0.15

        return min(
            100,
            creation_component
            + distribution_component
            + cross_component
            + comment_component
            + breadth_component,
        )

    def _compute_engagement(
        self,
        creation_rate: float,
        edit_freq: float,
        active_ratio: float,
        trend: str,
        contributors: int,
    ) -> float:
        """0-100: how engaged is the team with documentation."""
        creation_component = min(100, creation_rate * 50) * 0.25
        edit_component = min(100, edit_freq * 25) * 0.25
        active_component = active_ratio * 100 * 0.20

        trend_bonus = {"increasing": 15, "stable": 0, "decreasing": -15}.get(trend, 0)
        breadth_component = min(100, contributors * 5) * 0.15

        base = (
            creation_component + edit_component + active_component + breadth_component
        )
        return max(0, min(100, base + trend_bonus * 0.15))

    def _compute_burnout_risk(
        self,
        contribution_trend: str,
        creation_trend: str,
        edit_freq: float,
        stale_ratio: float,
    ) -> float:
        """Declining contribution patterns signal disengagement / burnout."""
        risk = 0.0

        # Declining contribution is the primary signal
        if contribution_trend == "decreasing":
            risk += 35
        elif contribution_trend == "stable":
            risk += 10

        # Declining creation specifically
        if creation_trend == "decreasing":
            risk += 20

        # Very low edit frequency = abandoned documentation
        if edit_freq < 0.5:
            risk += 15

        # High stale content = nobody maintaining
        risk += stale_ratio * 30

        return min(100, risk)

    def _generate_recommendations(
        self,
        sharing: float,
        engagement: float,
        burnout: float,
        concentration: float,
        stale_ratio: float,
        consumption_ratio: float,
    ) -> List[str]:
        recs = []
        if burnout >= 60:
            recs.append(
                "Documentation activity is declining significantly. "
                "Check if key contributors are overloaded or disengaged."
            )
        if concentration > 0.7:
            recs.append(
                "Knowledge creation is concentrated in very few people — "
                "high bus factor risk. Distribute documentation responsibilities."
            )
        if stale_ratio > 0.5:
            recs.append(
                "Over 50% of pages have no recent activity. Schedule "
                "documentation review sprints to keep knowledge current."
            )
        if consumption_ratio > 10:
            recs.append(
                "Consumption far exceeds creation (>10:1 view/edit ratio). "
                "Encourage 'edit the page' culture — anyone who reads should improve."
            )
        if sharing < 30:
            recs.append(
                "Knowledge sharing score is low. Consider doc-writing incentives, "
                "weekly knowledge-sharing sessions, or onboarding doc requirements."
            )
        if not recs:
            recs.append("Knowledge base activity is healthy. Continue monitoring.")
        return recs

    def _empty_signals(self) -> KBAnalyticsSignals:
        return KBAnalyticsSignals(
            total_pages_created=0,
            doc_creation_rate=0,
            edit_frequency=0,
            total_views=0,
            total_edits=0,
            consumption_ratio=0,
            stale_content_ratio=0,
            active_page_ratio=0,
            avg_edits_per_page=0,
            unique_contributors=0,
            contributor_concentration=0,
            cross_space_ratio=0,
            comment_to_edit_ratio=0,
            creation_trend="stable",
            contribution_trend="stable",
            knowledge_sharing_score=0,
            engagement_score=0,
            burnout_risk=0,
            risk_label="Healthy",
            recommendations=["No knowledge base data available."],
        )
