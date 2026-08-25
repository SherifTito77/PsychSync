"""
Data Source Aggregator — Wires connector outputs into intelligence engines.

Acts as the mediator between standalone data connectors (HRIS, Calendar,
Work Systems, Communication) and intelligence engines (BI, ONA, Pulse).

Each connector already normalizes external data. This service:
  1. Collects outputs from all registered connectors
  2. Transforms them into formats each intelligence engine accepts
  3. Feeds BI enrichment via build_enrichment()
  4. Feeds ONA edges from communication + work system collaboration
  5. Feeds HRIS behavioral signals to Pulse/Executive Intelligence
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DataSourceAggregator:
    """Collects and transforms connector outputs for intelligence engines."""

    def __init__(self):
        self._hris_registry = None
        self._calendar_registry = None
        self._work_systems_registry = None
        self._communication_registry = None

    def _load_registries(self):
        """Lazy-load registries to avoid import-time failures."""
        if self._hris_registry is not None:
            return

        try:
            from app.services.enterprise_hris_service import (
                HRISBehavioralAnalyzer,
                hris_registry,
            )

            self._hris_registry = hris_registry
            self._hris_analyzer = HRISBehavioralAnalyzer()
        except ImportError:
            logger.debug("HRIS service not available")
            self._hris_registry = None
            self._hris_analyzer = None

        try:
            from app.services.calendar_integration_service import (
                CalendarBehavioralAnalyzer,
                calendar_registry,
            )

            self._calendar_registry = calendar_registry
            self._calendar_analyzer = CalendarBehavioralAnalyzer()
        except ImportError:
            logger.debug("Calendar service not available")
            self._calendar_registry = None
            self._calendar_analyzer = None

        try:
            from app.services.work_systems_integration_service import (
                WorkSystemBehavioralAnalyzer,
                work_systems_registry,
            )

            self._work_systems_registry = work_systems_registry
            self._work_analyzer = WorkSystemBehavioralAnalyzer()
        except ImportError:
            logger.debug("Work Systems service not available")
            self._work_systems_registry = None
            self._work_analyzer = None

        try:
            from app.services.communication_analytics_service import (
                CommunicationHealthAnalyzer,
                communication_registry,
            )

            self._communication_registry = communication_registry
            self._communication_analyzer = CommunicationHealthAnalyzer()
        except ImportError:
            logger.debug("Communication Analytics service not available")
            self._communication_registry = None
            self._communication_analyzer = None

    # ── BI Enrichment Pipeline ───────────────────────────────────────

    async def gather_bi_enrichment(
        self,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Gather signals from all connectors and build BI enrichment dict.

        Returns the enrichment dict ready to pass to
        BehavioralIntelligenceService.get_organization_dashboard(enrichment=...).
        """
        self._load_registries()

        from app.services.behavioral_intelligence_service import (
            BehavioralIntelligenceService,
        )

        workload_snapshots = await self._gather_workload_snapshots(organization_id)
        cycle_times = await self._gather_cycle_times(organization_id)
        collaboration_edges = await self._gather_work_collaboration(organization_id)
        meeting_health = await self._gather_meeting_health(organization_id)

        enrichment = BehavioralIntelligenceService.build_enrichment(
            workload_snapshots=workload_snapshots,
            cycle_times=cycle_times,
            collaboration_edges=collaboration_edges,
            meeting_health=meeting_health,
        )

        # Augment with HRIS behavioral signals (tenure, leave, performance)
        hris_signals = await self._gather_hris_signals(organization_id)
        if hris_signals:
            enrichment["hris_signals"] = hris_signals
            if hris_signals.get("avg_tenure_days"):
                enrichment["avg_tenure_days"] = hris_signals["avg_tenure_days"]
            if hris_signals.get("avg_leave_utilization_pct"):
                enrichment["leave_utilization_pct"] = hris_signals[
                    "avg_leave_utilization_pct"
                ]
            if hris_signals.get("avg_performance_score"):
                enrichment["performance_score"] = hris_signals["avg_performance_score"]

        sources = []
        if workload_snapshots:
            sources.append("work_systems")
        if cycle_times and cycle_times.get("count", 0) > 0:
            sources.append("work_systems_cycle")
        if meeting_health is not None:
            sources.append("calendar")
        if hris_signals and hris_signals.get("total_employees", 0) > 0:
            sources.append("hris")
        if collaboration_edges:
            sources.append("work_collaboration")

        enrichment["_sources"] = sources
        enrichment["_source_count"] = len(sources)

        logger.info(
            "DataSourceAggregator: gathered enrichment from %d sources: %s",
            len(sources),
            sources,
        )

        return enrichment

    # ── ONA Edge Pipeline ────────────────────────────────────────────

    async def gather_ona_edges(
        self,
        organization_id: str,
    ) -> List[Dict[str, Any]]:
        """Gather collaboration edges from communication + work systems.

        Returns edge dicts compatible with ONA service edge construction:
          [{"source_email": ..., "target_email": ..., "weight": ..., "edge_type": ...}, ...]
        """
        self._load_registries()
        edges: List[Dict[str, Any]] = []

        # Work system collaboration (shared sprints/projects)
        work_edges = await self._gather_work_collaboration(organization_id)
        for e in work_edges:
            edges.append(
                {
                    "source_email": e["person_a"],
                    "target_email": e["person_b"],
                    "weight": min(1.0, e["shared_contexts"] / 5),
                    "edge_type": "work_system",
                }
            )

        # Communication edges (shared channel activity)
        comm_edges = await self._gather_communication_edges(organization_id)
        for e in comm_edges:
            edges.append(
                {
                    "source_email": e["person_a"],
                    "target_email": e["person_b"],
                    "weight": min(1.0, e["interaction_count"] / 20),
                    "edge_type": "communication",
                }
            )

        logger.info(
            "DataSourceAggregator: gathered %d ONA edges (%d work, %d communication)",
            len(edges),
            len(work_edges),
            len(comm_edges),
        )

        return edges

    # ── HRIS Signals for Pulse/Executive Intelligence ────────────────

    async def gather_hris_analysis(
        self,
        organization_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Full HRIS behavioral analysis for consumption by Pulse engine."""
        return await self._gather_hris_signals(organization_id)

    # ── Private: individual connector calls ──────────────────────────

    async def _gather_workload_snapshots(self, org_id: str) -> list:
        if not self._work_systems_registry:
            return []
        try:
            connectors = self._work_systems_registry.list_connectors()
            if not connectors:
                return []
            # Use first registered connector
            connector = connectors[0]
            items = await connector.fetch_items()
            return self._work_analyzer.analyze_workload(items)
        except Exception as exc:
            logger.warning("Failed to gather workload snapshots: %s", exc)
            return []

    async def _gather_cycle_times(self, org_id: str) -> Optional[Dict[str, Any]]:
        if not self._work_systems_registry:
            return None
        try:
            connectors = self._work_systems_registry.list_connectors()
            if not connectors:
                return None
            connector = connectors[0]
            items = await connector.fetch_items()
            return self._work_analyzer.analyze_cycle_times(items)
        except Exception as exc:
            logger.warning("Failed to gather cycle times: %s", exc)
            return None

    async def _gather_work_collaboration(self, org_id: str) -> list:
        if not self._work_systems_registry:
            return []
        try:
            connectors = self._work_systems_registry.list_connectors()
            if not connectors:
                return []
            connector = connectors[0]
            items = await connector.fetch_items()
            return self._work_analyzer.collaboration_from_items(items)
        except Exception as exc:
            logger.warning("Failed to gather work collaboration edges: %s", exc)
            return []

    async def _gather_meeting_health(self, org_id: str):
        if not self._calendar_registry:
            return None
        try:
            connectors = self._calendar_registry.list_connectors()
            if not connectors:
                return None
            connector = connectors[0]
            events = await connector.fetch_events(days=14)
            return self._calendar_analyzer.analyze_meeting_health(events, days=14)
        except Exception as exc:
            logger.warning("Failed to gather meeting health: %s", exc)
            return None

    async def _gather_hris_signals(self, org_id: str) -> Optional[Dict[str, Any]]:
        if not self._hris_registry:
            return None
        try:
            connectors = self._hris_registry.list_connectors()
            if not connectors:
                return None
            connector = connectors[0]
            employees = await connector.fetch_employees()
            return self._hris_analyzer.analyze(employees)
        except Exception as exc:
            logger.warning("Failed to gather HRIS signals: %s", exc)
            return None

    async def _gather_communication_edges(self, org_id: str) -> List[Dict[str, Any]]:
        """Derive person-to-person edges from shared channel co-activity."""
        if not self._communication_registry:
            return []
        try:
            connectors = self._communication_registry.list_connectors()
            if not connectors:
                return []
            connector = connectors[0]
            user_stats = await connector.fetch_user_stats()

            # Build edges: users active in the same channels interact
            channel_users: Dict[str, List[str]] = {}
            for stat in user_stats:
                # channels_active is a count, but we can infer co-presence
                # from users with overlapping high-activity patterns
                email = stat.user_email
                if email:
                    # Group by activity level buckets as a proxy
                    bucket = f"activity_{stat.channels_active}"
                    if bucket not in channel_users:
                        channel_users[bucket] = []
                    channel_users[bucket].append(email)

            # Also use thread-based interaction as stronger signal
            # Users who start and reply to threads are interacting
            thread_pairs: Dict[tuple, int] = {}
            active_users = [s for s in user_stats if s.threads_replied > 0]
            starters = [s for s in user_stats if s.threads_started > 0]

            for starter in starters:
                for replier in active_users:
                    if starter.user_email != replier.user_email:
                        pair = tuple(sorted([starter.user_email, replier.user_email]))
                        # Weight by min of their thread activity
                        weight = min(starter.threads_started, replier.threads_replied)
                        thread_pairs[pair] = thread_pairs.get(pair, 0) + weight

            return [
                {
                    "person_a": a,
                    "person_b": b,
                    "interaction_count": count,
                }
                for (a, b), count in sorted(
                    thread_pairs.items(), key=lambda x: x[1], reverse=True
                )[:50]
            ]
        except Exception as exc:
            logger.warning("Failed to gather communication edges: %s", exc)
            return []

    # ── Connectivity status ──────────────────────────────────────────

    def get_data_source_status(self) -> Dict[str, Any]:
        """Report which data sources are connected and available."""
        self._load_registries()
        status = {}
        for name, registry in [
            ("hris", self._hris_registry),
            ("calendar", self._calendar_registry),
            ("work_systems", self._work_systems_registry),
            ("communication", self._communication_registry),
        ]:
            if registry is None:
                status[name] = {"available": False, "reason": "Service not loaded"}
            else:
                try:
                    connectors = registry.list_connectors()
                    status[name] = {
                        "available": len(connectors) > 0,
                        "connector_count": len(connectors),
                    }
                except Exception:
                    status[name] = {"available": False, "reason": "Registry error"}
        return status


# Module-level singleton
data_source_aggregator = DataSourceAggregator()
