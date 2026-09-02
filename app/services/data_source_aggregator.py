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
        self._metadata_registries_loaded = False
        self._toxicity_registries_loaded = False

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

        # Metadata intelligence burnout signals
        metadata_signals = await self.gather_metadata_burnout_signals(
            organization_id,
            days=14,
        )
        if metadata_signals.get("_metadata_source_count", 0) > 0:
            enrichment["metadata_signals"] = metadata_signals
            if "metadata_burnout_risk" in metadata_signals:
                enrichment["metadata_burnout_risk"] = metadata_signals[
                    "metadata_burnout_risk"
                ]
            if "metadata_boundary_erosion" in metadata_signals:
                enrichment["metadata_boundary_erosion"] = metadata_signals[
                    "metadata_boundary_erosion"
                ]

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
        if metadata_signals.get("_metadata_source_count", 0) > 0:
            sources.append("metadata_intelligence")

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

    # ── Pulse Survey Signals ─────────────────────────────────────────

    async def gather_pulse_survey_signals(
        self,
        db,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Gather pulse survey aggregates for BI enrichment.

        Returns org-wide averaged scores (0-100) from direct employee
        self-report, ready to blend with inferred BI scores.
        """
        try:
            from app.services.pulse_survey_service import pulse_survey_service

            return await pulse_survey_service.get_org_pulse_summary(
                db, organization_id, lookback_days
            )
        except Exception as exc:
            logger.warning("Failed to gather pulse survey signals: %s", exc)
            return {}

    # ── Anonymous Feedback Signals ────────────────────────────────────

    async def gather_feedback_signals(
        self,
        db,
        organization_id: str,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """Gather anonymous feedback patterns as intelligence signals.

        Returns aggregated category counts and severity distribution
        for consumption by Pulse (friction, change impact) and BI
        (psych_safety) engines.
        """
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import and_, func, select

            from app.db.models.anonymous_feedback import AnonymousFeedback

            since = datetime.utcnow() - timedelta(days=lookback_days)

            result = await db.execute(
                select(
                    AnonymousFeedback.category,
                    AnonymousFeedback.severity,
                    func.count(AnonymousFeedback.id),
                )
                .where(
                    and_(
                        AnonymousFeedback.organization_id == organization_id,
                        AnonymousFeedback.submitted_at >= since,
                    )
                )
                .group_by(AnonymousFeedback.category, AnonymousFeedback.severity)
            )
            rows = result.all()

            if not rows:
                return {}

            total = sum(r[2] for r in rows)
            category_counts: Dict[str, int] = {}
            severity_counts: Dict[str, int] = {}
            for category, severity, count in rows:
                category_counts[category] = category_counts.get(category, 0) + count
                severity_counts[severity] = severity_counts.get(severity, 0) + count

            critical_high = severity_counts.get("critical", 0) + severity_counts.get(
                "high", 0
            )
            concern_ratio = critical_high / total if total else 0

            # Friction signal: toxic_behavior + team_dynamics + leadership reports
            friction_categories = {
                "toxic_behavior",
                "team_dynamics",
                "leadership_concerns",
            }
            friction_reports = sum(
                category_counts.get(c, 0) for c in friction_categories
            )

            # Psych safety signal: psychological_safety + discrimination reports
            safety_categories = {"psychological_safety", "discrimination_bias"}
            safety_reports = sum(category_counts.get(c, 0) for c in safety_categories)

            # Change impact signal: workplace_environment (stress/burnout/culture)
            change_reports = category_counts.get("workplace_environment", 0)

            return {
                "total_reports": total,
                "concern_ratio": round(concern_ratio, 3),
                "friction_reports": friction_reports,
                "safety_reports": safety_reports,
                "change_reports": change_reports,
                "category_breakdown": category_counts,
                "severity_breakdown": severity_counts,
            }

        except Exception as exc:
            logger.warning("Failed to gather feedback signals: %s", exc)
            return {}

    # ── Culture Metrics Signals ────────────────────────────────────────

    async def gather_culture_signals(
        self,
        db,
        organization_id: str,
        lookback_days: int = 30,
    ) -> Dict[str, Any]:
        """Gather recent CultureMetrics as direct signals for BI scoring.

        Returns team-level culture scores for psych_safety, collaboration,
        and friction enrichment.
        """
        try:
            from datetime import date, timedelta

            from sqlalchemy import and_, select

            from app.db.models.culture_metrics import CultureMetrics

            since = date.today() - timedelta(days=lookback_days)

            result = await db.execute(
                select(CultureMetrics)
                .where(
                    and_(
                        CultureMetrics.organization_id == organization_id,
                        CultureMetrics.metric_date >= since,
                    )
                )
                .order_by(CultureMetrics.metric_date.desc())
            )
            metrics = result.scalars().all()

            if not metrics:
                return {}

            # Aggregate across all recent entries
            psych_safety_scores = [
                float(m.psychological_safety_score)
                for m in metrics
                if m.psychological_safety_score is not None
            ]
            collab_scores = [
                float(m.collaboration_effectiveness)
                for m in metrics
                if m.collaboration_effectiveness is not None
            ]
            morale_scores = [
                float(m.overall_morale_score)
                for m in metrics
                if m.overall_morale_score is not None
            ]
            conflict_levels = [
                m.conflict_level for m in metrics if m.conflict_level is not None
            ]

            signals: Dict[str, Any] = {}
            if psych_safety_scores:
                signals["culture_psych_safety"] = round(
                    sum(psych_safety_scores) / len(psych_safety_scores), 1
                )
            if collab_scores:
                signals["culture_collaboration"] = round(
                    sum(collab_scores) / len(collab_scores), 1
                )
            if morale_scores:
                signals["culture_morale"] = round(
                    sum(morale_scores) / len(morale_scores), 1
                )
            if conflict_levels:
                conflict_map = {"low": 20, "medium": 50, "high": 75, "critical": 95}
                conflict_values = [conflict_map.get(c, 50) for c in conflict_levels]
                signals["culture_conflict"] = round(
                    sum(conflict_values) / len(conflict_values), 1
                )

            return signals

        except Exception as exc:
            logger.warning("Failed to gather culture signals: %s", exc)
            return {}

    # ── Peer Recognition Signals ──────────────────────────────────────

    async def gather_recognition_signals(
        self,
        db,
        organization_id: str,
        lookback_days: int = 90,
    ) -> Dict[str, Any]:
        """Gather peer recognition patterns per manager (recognition given to team).

        Returns per-manager recognition counts for manager effectiveness scoring.
        """
        try:
            from datetime import datetime, timedelta

            from sqlalchemy import and_, func, select

            from app.db.models.peer_recognition import PeerRecognition

            since = datetime.utcnow() - timedelta(days=lookback_days)

            result = await db.execute(
                select(
                    PeerRecognition.giver_id,
                    func.count(PeerRecognition.id),
                    func.count(func.distinct(PeerRecognition.receiver_id)),
                )
                .where(
                    and_(
                        PeerRecognition.organization_id == organization_id,
                        PeerRecognition.created_at >= since,
                    )
                )
                .group_by(PeerRecognition.giver_id)
            )
            rows = result.all()

            if not rows:
                return {}

            per_giver = {}
            total_given = 0
            total_unique_receivers = 0
            for giver_id, count, unique_receivers in rows:
                per_giver[str(giver_id)] = {
                    "given_count": count,
                    "unique_receivers": unique_receivers,
                }
                total_given += count
                total_unique_receivers += unique_receivers

            return {
                "total_recognitions": total_given,
                "unique_givers": len(per_giver),
                "per_giver": per_giver,
            }

        except Exception as exc:
            logger.warning("Failed to gather recognition signals: %s", exc)
            return {}

    async def gather_meeting_signals(
        self,
        db: "AsyncSession",
        organization_id: str,
        lookback_days: int = 30,
    ) -> Optional[Dict[str, Any]]:
        """Gather meeting effectiveness signals for BI enrichment."""
        try:
            from app.services.meeting_effectiveness_service import (
                meeting_effectiveness_service,
            )

            return await meeting_effectiveness_service.get_meeting_signals(
                db, organization_id, lookback_days
            )
        except Exception as e:
            logger.debug("Meeting signals unavailable: %s", e)
            return None

    async def gather_360_feedback_signals(
        self,
        db: "AsyncSession",
        organization_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Gather 360-feedback signals for BI/Digital Twin integration."""
        try:
            from app.services.feedback_360_service import feedback_360_service

            return await feedback_360_service.get_feedback_signals(db, organization_id)
        except Exception as e:
            logger.debug("360 feedback signals unavailable: %s", e)
            return None

    # ── Connectivity status ──────────────────────────────────────────

    async def gather_okr_signals(
        self,
        db: "AsyncSession",
        organization_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Gather OKR progress signals for intelligence engine enrichment.

        Returns:
            Dict with at_risk_count, off_track_count, achievement_rate,
            capacity_pressure (proxy for team overload from OKR density).
        """
        try:
            from sqlalchemy import and_, func, select

            from app.db.models.okr import KeyResult, KRStatus, Objective, OKRStatus

            # Get active objectives for this org
            result = await db.execute(
                select(
                    func.count(Objective.id).label("total"),
                    func.count(Objective.id)
                    .filter(Objective.health_risk_flag == "critical")
                    .label("critical"),
                    func.count(Objective.id)
                    .filter(Objective.health_risk_flag == "warning")
                    .label("warning"),
                ).where(
                    and_(
                        Objective.organization_id == organization_id,
                        Objective.status == OKRStatus.ACTIVE,
                    )
                )
            )
            row = result.one_or_none()
            if not row or row.total == 0:
                return None

            # Get KR status breakdown
            kr_result = await db.execute(
                select(
                    func.count(KeyResult.id).label("total_krs"),
                    func.count(KeyResult.id)
                    .filter(KeyResult.status == KRStatus.AT_RISK)
                    .label("at_risk"),
                    func.count(KeyResult.id)
                    .filter(KeyResult.status == KRStatus.OFF_TRACK)
                    .label("off_track"),
                    func.count(KeyResult.id)
                    .filter(KeyResult.status == KRStatus.ACHIEVED)
                    .label("achieved"),
                )
                .join(Objective, Objective.id == KeyResult.objective_id)
                .where(
                    and_(
                        Objective.organization_id == organization_id,
                        Objective.status == OKRStatus.ACTIVE,
                    )
                )
            )
            kr = kr_result.one_or_none()

            total_krs = kr.total_krs if kr else 0
            achievement_rate = (
                round(kr.achieved / total_krs * 100, 1) if total_krs > 0 else 0
            )

            # Capacity pressure: high OKR density per team = overload risk
            # Many at-risk/off-track KRs signal capacity problems
            at_risk_ratio = (
                (kr.at_risk + kr.off_track) / total_krs if total_krs > 0 else 0
            )
            capacity_pressure = min(100, at_risk_ratio * 150)

            return {
                "active_objectives": row.total,
                "critical_health": row.critical,
                "warning_health": row.warning,
                "total_krs": total_krs,
                "at_risk_krs": kr.at_risk if kr else 0,
                "off_track_krs": kr.off_track if kr else 0,
                "achievement_rate": achievement_rate,
                "capacity_pressure": round(capacity_pressure, 1),
            }

        except Exception as e:
            logger.debug("OKR signals unavailable: %s", e)
            return None

    # ── Metadata Intelligence Signals ──────────────────────────────

    def _load_metadata_registries(self):
        """Lazy-load metadata intelligence registries."""
        if self._metadata_registries_loaded:
            return
        self._metadata_registries_loaded = True

        self._metadata_sources: Dict[str, Any] = {}

        registry_imports = [
            (
                "email",
                "app.services.email_metadata_service",
                "email_metadata_registry",
                "EmailMetadataAnalyzer",
            ),
            (
                "slack",
                "app.services.slack_metadata_service",
                "slack_metadata_registry",
                "SlackMetadataAnalyzer",
            ),
            (
                "teams",
                "app.services.teams_metadata_service",
                "teams_metadata_registry",
                "TeamsMetadataAnalyzer",
            ),
            (
                "computer_usage",
                "app.services.computer_usage_metadata_service",
                "computer_usage_registry",
                "ComputerUsageAnalyzer",
            ),
            (
                "badge_access",
                "app.services.badge_access_metadata_service",
                "badge_access_registry",
                "BadgeAccessAnalyzer",
            ),
            (
                "pto_patterns",
                "app.services.pto_patterns_metadata_service",
                "pto_registry",
                "PTOPatternsAnalyzer",
            ),
            (
                "git",
                "app.services.git_metadata_service",
                "git_metadata_registry",
                "GitMetadataAnalyzer",
            ),
            (
                "video_conference",
                "app.services.video_conference_metadata_service",
                "video_conference_registry",
                "VideoConferenceAnalyzer",
            ),
            (
                "knowledge_base",
                "app.services.knowledge_base_metadata_service",
                "kb_analytics_registry",
                "KBAnalyticsAnalyzer",
            ),
        ]

        for name, module_path, registry_name, analyzer_name in registry_imports:
            try:
                import importlib

                mod = importlib.import_module(module_path)
                self._metadata_sources[name] = {
                    "registry": getattr(mod, registry_name),
                    "analyzer": getattr(mod, analyzer_name)(),
                }
            except Exception:
                logger.debug("Metadata source %s not available", name)

    async def gather_metadata_burnout_signals(
        self,
        organization_id: str,
        user_email: Optional[str] = None,
        days: int = 14,
    ) -> Dict[str, Any]:
        """Gather burnout signals from all metadata intelligence sources.

        Returns a normalized dict with per-source burnout scores and a
        composite metadata_burnout_risk for BI/Pulse engine consumption.

        Each source contributes:
          - {source}_burnout_risk (0-100)
          - {source}_risk_label
          - {source}_boundary_erosion (0-100)
        """
        self._load_metadata_registries()

        from dataclasses import asdict
        from datetime import datetime, timedelta

        signals: Dict[str, Any] = {}
        active_sources: List[str] = []
        burnout_scores: List[float] = []
        boundary_scores: List[float] = []

        end = datetime.utcnow()
        start = end - timedelta(days=days)

        for source_name, source in self._metadata_sources.items():
            registry = source["registry"]
            analyzer = source["analyzer"]

            connectors = registry.list_connectors()
            if not connectors:
                continue

            try:
                result = await self._fetch_metadata_signals(
                    source_name,
                    registry,
                    analyzer,
                    user_email=user_email,
                    org_id=organization_id,
                    start=start,
                    end=end,
                    days=days,
                )
                if result:
                    signals[f"{source_name}_burnout_risk"] = result.get(
                        "burnout_risk_score", 0
                    )
                    signals[f"{source_name}_risk_label"] = result.get(
                        "risk_label", "No Data"
                    )
                    signals[f"{source_name}_boundary_erosion"] = result.get(
                        "boundary_erosion_score", 0
                    )

                    # Store quality degradation from git CI metrics
                    if (
                        source_name == "git"
                        and result.get("quality_degradation_score") is not None
                    ):
                        signals["git_quality_degradation"] = result.get(
                            "quality_degradation_score", 0
                        )

                    # Store calendar fragmentation granular score
                    if (
                        source_name == "calendar"
                        and result.get("fragmentation_score") is not None
                    ):
                        signals["calendar_fragmentation_score"] = result.get(
                            "fragmentation_score", 0
                        )
                        signals["calendar_focus_hours_per_week"] = result.get(
                            "focus_hours_per_week", 0
                        )
                        signals["calendar_back_to_back_rate"] = result.get(
                            "back_to_back_rate", 0
                        )

                    burnout_scores.append(result.get("burnout_risk_score", 0))
                    boundary_scores.append(result.get("boundary_erosion_score", 0))
                    active_sources.append(source_name)
            except Exception as exc:
                logger.warning("Metadata source %s failed: %s", source_name, exc)

        # Composite: weighted average with PTO getting extra weight (strongest predictor)
        if burnout_scores:
            weights = []
            for src in active_sources:
                weights.append(1.5 if src == "pto_patterns" else 1.0)
            total_weight = sum(weights)
            composite = (
                sum(s * w for s, w in zip(burnout_scores, weights)) / total_weight
            )
            avg_boundary = sum(boundary_scores) / len(boundary_scores)

            signals["metadata_burnout_risk"] = round(composite, 1)
            signals["metadata_boundary_erosion"] = round(avg_boundary, 1)
            signals["metadata_risk_label"] = (
                "Critical"
                if composite >= 70
                else (
                    "Elevated"
                    if composite >= 45
                    else "Monitor" if composite >= 25 else "Healthy"
                )
            )

        signals["_metadata_sources"] = active_sources
        signals["_metadata_source_count"] = len(active_sources)

        logger.info(
            "DataSourceAggregator: gathered metadata signals from %d sources: %s",
            len(active_sources),
            active_sources,
        )
        return signals

    async def _fetch_metadata_signals(
        self,
        source_name: str,
        registry,
        analyzer,
        user_email: Optional[str],
        org_id: Optional[str] = None,
        start=None,
        end=None,
        days: int = 14,
    ) -> Optional[Dict[str, Any]]:
        """Fetch and analyze metadata from a single source."""
        from dataclasses import asdict

        connector_list = registry.list_connectors()
        if not connector_list:
            return None

        connector = registry.get(connector_list[0]["name"])
        if not connector:
            return None

        try:
            if source_name == "email":
                records = await connector.fetch_metadata(
                    user_email=user_email or "",
                    start=start,
                    end=end,
                )
                from app.services.email_metadata_service import EmailMetadataAnalyzer

                records = EmailMetadataAnalyzer.compute_response_times(records)
                signals = analyzer.analyze(records, days=days)
            elif source_name == "slack":
                activity = await connector.fetch_activity(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                presence = await connector.fetch_presence(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(activity, presence, days=days)
            elif source_name == "teams":
                activity = await connector.fetch_activity(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                presence = await connector.fetch_presence(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(activity, presence, days=days)
            elif source_name == "computer_usage":
                buckets = await connector.fetch_buckets(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(buckets, days=days)
            elif source_name == "badge_access":
                swipes = await connector.fetch_swipes(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(swipes, days=days)
            elif source_name == "pto_patterns":
                records = await connector.fetch_leave_records(
                    user_id=user_email or "",
                    start=start.date(),
                    end=end.date(),
                )
                balance = await connector.fetch_balance(
                    user_id=user_email or "",
                )
                signals = analyzer.analyze(records, balance, lookback_days=days)
            elif source_name == "git":
                commits = await connector.fetch_commits(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                prs = await connector.fetch_prs(
                    user_id=user_email or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(commits, prs, days=days)
            elif source_name == "video_conference":
                meetings = await connector.fetch_meetings(
                    org_id=org_id or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(meetings, days=days)
            elif source_name == "knowledge_base":
                activity = await connector.fetch_activity(
                    org_id=org_id or "",
                    start=start,
                    end=end,
                )
                signals = analyzer.analyze(activity, days=days)
            else:
                return None

            return asdict(signals)
        except Exception as exc:
            logger.debug("Metadata %s analysis failed: %s", source_name, exc)
            return None

    # ── Toxicity & Burnout Signal Collectors ─────────────────────

    def _load_toxicity_registries(self):
        """Lazy-load toxicity + passive burnout signal registries."""
        if self._toxicity_registries_loaded:
            return
        self._toxicity_registries_loaded = True

        self._toxicity_sources: Dict[str, Any] = {}
        self._burnout_sources: Dict[str, Any] = {}

        # Toxicity collectors
        toxicity_imports = [
            (
                "calendar_toxicity",
                "app.services.calendar_toxicity_service",
                "calendar_toxicity_registry",
                "CalendarToxicityAnalyzer",
            ),
            (
                "code_review",
                "app.services.code_review_toxicity_service",
                "code_review_toxicity_registry",
                "CodeReviewToxicityAnalyzer",
            ),
            (
                "ticket_queue",
                "app.services.ticket_metadata_service",
                "ticket_toxicity_registry",
                "TicketToxicityAnalyzer",
            ),
            (
                "communication",
                "app.services.communication_toxicity_service",
                "communication_toxicity_registry",
                "CommunicationToxicityAnalyzer",
            ),
        ]

        # Passive burnout collectors (SSO, VPN, Endpoint)
        burnout_imports = [
            (
                "sso",
                "app.services.sso_metadata_service",
                "sso_metadata_registry",
                "SSOMetadataAnalyzer",
            ),
            (
                "vpn",
                "app.services.vpn_metadata_service",
                "vpn_metadata_registry",
                "VPNMetadataAnalyzer",
            ),
            (
                "endpoint",
                "app.services.endpoint_metadata_service",
                "endpoint_metadata_registry",
                "EndpointMetadataAnalyzer",
            ),
        ]

        for name, module_path, registry_name, analyzer_name in toxicity_imports:
            try:
                import importlib

                mod = importlib.import_module(module_path)
                self._toxicity_sources[name] = {
                    "registry": getattr(mod, registry_name),
                    "analyzer": getattr(mod, analyzer_name)(),
                }
            except Exception:
                logger.debug("Toxicity source %s not available", name)

        for name, module_path, registry_name, analyzer_name in burnout_imports:
            try:
                import importlib

                mod = importlib.import_module(module_path)
                self._burnout_sources[name] = {
                    "registry": getattr(mod, registry_name),
                    "analyzer": getattr(mod, analyzer_name)(),
                }
            except Exception:
                logger.debug("Burnout source %s not available", name)

    async def gather_toxicity_signals(
        self,
        organization_id: str,
        org_emails: Optional[List[str]] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Gather toxicity signals from all toxicity collectors.

        Returns per-source toxicity scores and a composite.
        """
        self._load_toxicity_registries()

        from dataclasses import asdict
        from datetime import datetime, timedelta

        signals: Dict[str, Any] = {}
        active_sources: List[str] = []
        toxicity_scores: List[float] = []

        end = datetime.utcnow()
        start = end - timedelta(days=days)
        emails = org_emails or []

        for source_name, source in self._toxicity_sources.items():
            registry = source["registry"]
            analyzer = source["analyzer"]

            if not registry.list_connectors():
                continue

            try:
                result = await self._fetch_toxicity_signals(
                    source_name,
                    registry,
                    analyzer,
                    org_emails=emails,
                    start=start,
                    end=end,
                    days=days,
                )
                if result:
                    signals[f"{source_name}_toxicity_score"] = result.get(
                        "toxicity_score", 0
                    )
                    signals[f"{source_name}_risk_label"] = result.get(
                        "risk_label", "No Data"
                    )
                    # Store full per-signal breakdown for granular engine input
                    signals[f"{source_name}_signals"] = result
                    toxicity_scores.append(result.get("toxicity_score", 0))
                    active_sources.append(source_name)
            except Exception as exc:
                logger.warning("Toxicity source %s failed: %s", source_name, exc)

        if toxicity_scores:
            # Attrition clustering gets extra weight (strongest confirmation)
            weights = []
            for src in active_sources:
                weights.append(1.3 if src == "communication" else 1.0)
            total_weight = sum(weights)
            composite = (
                sum(s * w for s, w in zip(toxicity_scores, weights)) / total_weight
            )

            signals["composite_toxicity_score"] = round(composite, 1)
            signals["toxicity_risk_label"] = (
                "Critical"
                if composite >= 60
                else (
                    "Elevated"
                    if composite >= 35
                    else "Monitor" if composite >= 15 else "Healthy"
                )
            )

        signals["_toxicity_sources"] = active_sources
        signals["_toxicity_source_count"] = len(active_sources)

        logger.info(
            "DataSourceAggregator: gathered toxicity signals from %d sources: %s",
            len(active_sources),
            active_sources,
        )
        return signals

    async def gather_passive_burnout_signals(
        self,
        organization_id: str,
        user_email: Optional[str] = None,
        days: int = 14,
    ) -> Dict[str, Any]:
        """Gather passive burnout signals from SSO, VPN, Endpoint collectors.

        These sources require zero human input — pure infrastructure metadata.
        Complements existing metadata burnout signals (email, slack, etc.).
        """
        self._load_toxicity_registries()

        from dataclasses import asdict
        from datetime import datetime, timedelta

        signals: Dict[str, Any] = {}
        active_sources: List[str] = []
        burnout_scores: List[float] = []

        end = datetime.utcnow()
        start = end - timedelta(days=days)

        for source_name, source in self._burnout_sources.items():
            registry = source["registry"]
            analyzer = source["analyzer"]

            if not registry.list_connectors():
                continue

            try:
                connector_list = registry.list_connectors()
                connector = registry.get(connector_list[0]["name"])
                if not connector:
                    continue

                if source_name == "sso":
                    events = await connector.fetch_events(
                        user_email=user_email or "",
                        start=start,
                        end=end,
                    )
                    result = analyzer.analyze(events, days=days)
                elif source_name == "vpn":
                    sessions = await connector.fetch_sessions(
                        user_email=user_email or "",
                        start=start,
                        end=end,
                    )
                    result = analyzer.analyze(sessions, days=days)
                elif source_name == "endpoint":
                    activity = await connector.fetch_activity(
                        user_id=user_email or "",
                        start=start,
                        end=end,
                    )
                    result = analyzer.analyze(activity, days=days)
                else:
                    continue

                result_dict = asdict(result)
                signals[f"{source_name}_burnout_risk"] = result_dict.get(
                    "burnout_risk_score", 0
                )
                signals[f"{source_name}_risk_label"] = result_dict.get(
                    "risk_label", "No Data"
                )
                signals[f"{source_name}_boundary_erosion"] = result_dict.get(
                    "boundary_erosion_score", 0
                )

                burnout_scores.append(result_dict.get("burnout_risk_score", 0))
                active_sources.append(source_name)

                # Source-specific signals for the composite engine
                if source_name == "sso":
                    signals["login_span_expansion"] = result_dict.get(
                        "session_overextension_score", 0
                    )
                elif source_name == "endpoint":
                    signals["break_deficit"] = result_dict.get("break_deficit_score", 0)
                elif source_name == "vpn":
                    signals["after_hours_vpn"] = result_dict.get(
                        "boundary_erosion_score", 0
                    )

            except Exception as exc:
                logger.warning("Burnout source %s failed: %s", source_name, exc)

        if burnout_scores:
            composite = sum(burnout_scores) / len(burnout_scores)
            signals["passive_burnout_risk"] = round(composite, 1)
            signals["passive_burnout_label"] = (
                "Critical"
                if composite >= 70
                else (
                    "Elevated"
                    if composite >= 45
                    else "Monitor" if composite >= 25 else "Healthy"
                )
            )

        signals["_passive_burnout_sources"] = active_sources
        signals["_passive_burnout_source_count"] = len(active_sources)

        logger.info(
            "DataSourceAggregator: gathered passive burnout from %d sources: %s",
            len(active_sources),
            active_sources,
        )
        return signals

    async def gather_toxicity_burnout_composite(
        self,
        organization_id: str,
        org_emails: Optional[List[str]] = None,
        user_email: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Full toxicity + burnout composite with cross-contamination.

        Combines all signal sources into a unified risk assessment
        using the ToxicityBurnoutEngine.
        """
        from app.services.toxicity_burnout_engine import (
            BurnoutSignalInput,
            ToxicitySignalInput,
            compute_composite,
        )
        from dataclasses import asdict

        # Gather both signal families
        toxicity_raw = await self.gather_toxicity_signals(
            organization_id,
            org_emails=org_emails,
            days=days,
        )
        burnout_raw = await self.gather_passive_burnout_signals(
            organization_id,
            user_email=user_email,
            days=days,
        )
        metadata_raw = await self.gather_metadata_burnout_signals(
            organization_id,
            user_email=user_email,
            days=days,
        )

        # Build typed inputs for the engine
        burnout_input = BurnoutSignalInput(
            pto_avoidance=metadata_raw.get("pto_patterns_burnout_risk"),
            login_span_expansion=burnout_raw.get("login_span_expansion"),
            break_deficit=burnout_raw.get("break_deficit"),
            calendar_fragmentation=metadata_raw.get("calendar_fragmentation_score")
            or metadata_raw.get("calendar_burnout_risk"),
            after_hours_trend=burnout_raw.get("after_hours_vpn")
            or metadata_raw.get("email_burnout_risk"),
            quality_degradation=metadata_raw.get("git_quality_degradation")
            or metadata_raw.get("git_burnout_risk"),
        )

        # Extract granular per-signal scores (not the composite per-source)
        cal_signals = toxicity_raw.get("calendar_toxicity_signals", {})
        comm_signals = toxicity_raw.get("communication_signals", {})

        toxicity_input = ToxicitySignalInput(
            speaking_imbalance=cal_signals.get("speaking_imbalance_score")
            or toxicity_raw.get("calendar_toxicity_toxicity_score"),
            reaction_asymmetry=comm_signals.get("reaction_asymmetry_score")
            or toxicity_raw.get("communication_toxicity_score"),
            review_hostility=toxicity_raw.get("code_review_toxicity_score"),
            one_on_one_cancellation=cal_signals.get("selective_cancel_score")
            or cal_signals.get("one_on_one_cancel_rate"),
            invite_exclusion=cal_signals.get("exclusion_score"),
            response_asymmetry=comm_signals.get("latency_asymmetry_score"),
            attrition_clustering=comm_signals.get("attrition_cluster_score"),
        )

        result = compute_composite(burnout_input, toxicity_input)

        output = asdict(result)
        output["_raw_toxicity"] = toxicity_raw
        output["_raw_passive_burnout"] = burnout_raw
        output["_raw_metadata_burnout"] = metadata_raw

        return output

    async def _fetch_toxicity_signals(
        self,
        source_name: str,
        registry,
        analyzer,
        org_emails: List[str],
        start,
        end,
        days: int,
    ) -> Optional[Dict[str, Any]]:
        """Fetch and analyze toxicity signals from a single source."""
        from dataclasses import asdict

        connector_list = registry.list_connectors()
        if not connector_list:
            return None

        connector = registry.get(connector_list[0]["name"])
        if not connector:
            return None

        try:
            if source_name == "calendar_toxicity":
                meetings = await connector.fetch_meetings(
                    org_emails=org_emails,
                    start=start,
                    end=end,
                )
                recurring = await connector.fetch_recurring_history(
                    org_emails=org_emails,
                    start=start,
                    end=end,
                )
                result = analyzer.analyze(meetings, recurring, days=days)
            elif source_name == "code_review":
                reviews = await connector.fetch_reviews(
                    org_or_repo=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                result = analyzer.analyze(reviews, days=days)
            elif source_name == "ticket_queue":
                tickets = await connector.fetch_tickets(
                    project_or_team=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                result = analyzer.analyze(tickets, days=days)
            elif source_name == "communication":
                reactions = await connector.fetch_reaction_data(
                    org_id=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                latencies = await connector.fetch_response_latencies(
                    org_id=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                cc_patterns = await connector.fetch_cc_patterns(
                    org_id=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                departures = await connector.fetch_departures(
                    org_id=org_emails[0] if org_emails else "",
                    start=start,
                    end=end,
                )
                result = analyzer.analyze(reactions, latencies, cc_patterns, departures)
            else:
                return None

            return asdict(result)
        except Exception as exc:
            logger.debug("Toxicity %s analysis failed: %s", source_name, exc)
            return None

    def get_data_source_status(self) -> Dict[str, Any]:
        """Report which data sources are connected and available."""
        self._load_registries()
        self._load_metadata_registries()
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

        # Metadata Intelligence sources
        for name, source in self._metadata_sources.items():
            key = f"metadata_{name}"
            try:
                connectors = source["registry"].list_connectors()
                status[key] = {
                    "available": len(connectors) > 0,
                    "connector_count": len(connectors),
                }
            except Exception:
                status[key] = {"available": False, "reason": "Registry error"}

        # Toxicity sources
        self._load_toxicity_registries()
        for name, source in self._toxicity_sources.items():
            key = f"toxicity_{name}"
            try:
                connectors = source["registry"].list_connectors()
                status[key] = {
                    "available": len(connectors) > 0,
                    "connector_count": len(connectors),
                }
            except Exception:
                status[key] = {"available": False, "reason": "Registry error"}

        # Passive burnout sources (SSO, VPN, Endpoint)
        for name, source in self._burnout_sources.items():
            key = f"burnout_{name}"
            try:
                connectors = source["registry"].list_connectors()
                status[key] = {
                    "available": len(connectors) > 0,
                    "connector_count": len(connectors),
                }
            except Exception:
                status[key] = {"available": False, "reason": "Registry error"}

        return status


# Module-level singleton
data_source_aggregator = DataSourceAggregator()
