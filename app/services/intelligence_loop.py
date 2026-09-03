"""
Intelligence Loop Orchestrator -- the core product cycle.

This is PsychSync's brain. It runs the full closed-loop:
  Connect -> Collect -> Normalize -> Network -> Patterns -> Risks -> Explain -> Intervene -> Measure

Each cycle produces an IntelligenceCycleResult that represents the current
organizational health state with identified risks and recommended actions.
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ======================================================================
# DATA STRUCTURES
# ======================================================================


@dataclass
class RiskCard:
    """A single identified organizational risk with explanation and recommendation."""

    risk_id: str  # deterministic hash for deduplication
    risk_type: str  # "isolation", "burnout", "bottleneck", "silo", "turnover", etc.
    severity: str  # "low", "medium", "high", "critical"
    severity_score: float  # 0-100
    title: str  # "Team Alpha has 3 isolated employees"
    explanation: str  # 2-3 sentence natural language explanation
    contributing_signals: List[
        Dict[str, Any]
    ]  # [{source, signal_type, value, confidence}]
    affected_scope: str  # "individual", "team", "department", "organization"
    affected_id: str  # UUID of affected entity
    affected_name: str  # human-readable name
    recommendation: str  # "Schedule weekly team sync, assign buddy for onboarding"
    auto_action: Optional[str] = None  # action plan category if auto-creation warranted


@dataclass
class DataSourceStatus:
    """Status of a single data source in the intelligence pipeline."""

    name: str
    connected: bool
    last_updated: Optional[datetime] = None
    signal_count: int = 0
    health: str = "missing"  # "healthy", "stale", "missing"


@dataclass
class ImprovementMetric:
    """Tracks improvement on a metric tied to an active intervention."""

    metric_name: str
    baseline_value: float
    current_value: float
    delta: float  # current - baseline
    delta_percent: float  # (delta / baseline) * 100
    direction: str  # "improving", "stable", "worsening"
    intervention_id: Optional[str] = None


@dataclass
class IntelligenceCycleResult:
    """Complete output of one intelligence cycle."""

    org_id: str
    cycle_timestamp: datetime
    cycle_duration_ms: int

    # Stage 1-2: Connect & Collect
    data_sources: List[DataSourceStatus]
    total_signals_collected: int

    # Stage 3: Normalize
    signal_summary: Dict[str, float]  # category -> avg score

    # Stage 4: Network
    network_health: float  # 0-100
    network_signal_count: int

    # Stage 5-6: Patterns & Risks
    risks: List[RiskCard]
    risk_summary: Dict[str, int]  # severity -> count

    # Stage 7: Explanations
    narrative_summary: Optional[str]  # 1-paragraph summary

    # Stage 8-9: Interventions & Measurement
    active_interventions: int
    improvement_metrics: List[ImprovementMetric]
    overall_health_score: float  # 0-100 composite


# ======================================================================
# SEVERITY HELPERS
# ======================================================================

_SEVERITY_THRESHOLDS = [
    (75, "critical"),
    (55, "high"),
    (35, "medium"),
    (0, "low"),
]


def _severity_label(score: float) -> str:
    for threshold, label in _SEVERITY_THRESHOLDS:
        if score >= threshold:
            return label
    return "low"


def _risk_id(risk_type: str, scope: str, scope_id: str) -> str:
    """Deterministic hash for deduplication."""
    raw = f"{risk_type}:{scope}:{scope_id}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# Pattern type -> (risk_type, auto_action category, title template)
_PATTERN_RISK_MAP: Dict[str, tuple] = {
    "calendar_overload": (
        "overload",
        "wellness",
        "Calendar overload detected",
    ),
    "team_silos": (
        "silo",
        "collaboration",
        "Team silos forming",
    ),
    "burnout_risk": (
        "burnout",
        "wellness",
        "Burnout risk elevated",
    ),
    "career_stagnation": (
        "stagnation",
        "people",
        "Career stagnation signals",
    ),
    "knowledge_hoarding": (
        "bottleneck",
        "collaboration",
        "Knowledge concentrated in few individuals",
    ),
    "communication_overload": (
        "overload",
        "wellness",
        "Communication overload",
    ),
    "workload_spike": (
        "overload",
        "wellness",
        "Workload spike detected",
    ),
    "disengagement_drift": (
        "burnout",
        "wellness",
        "Disengagement drift pattern",
    ),
    "collaboration_bottleneck": (
        "bottleneck",
        "collaboration",
        "Collaboration bottleneck",
    ),
    "weekend_creep": (
        "burnout",
        "wellness",
        "Weekend work creep",
    ),
}


# ======================================================================
# ORCHESTRATOR
# ======================================================================


class IntelligenceLoopOrchestrator:
    """Runs the full intelligence cycle for an organization.

    Gracefully degrades when data sources are unavailable -- the cycle
    always completes, even if only partial data is present.
    """

    def __init__(self):
        self._aggregator = None
        self._normalization_service = None

    def _ensure_services(self):
        """Lazy-load service singletons to avoid import-time side effects."""
        if self._aggregator is None:
            from app.services.data_source_aggregator import data_source_aggregator

            self._aggregator = data_source_aggregator

        if self._normalization_service is None:
            from app.services.data_normalization_layer import data_normalization_service

            self._normalization_service = data_normalization_service

    # ------------------------------------------------------------------
    # MAIN ENTRY POINT
    # ------------------------------------------------------------------

    async def run_cycle(self, db: AsyncSession, org_id: str) -> IntelligenceCycleResult:
        """Execute one full intelligence cycle. This is the main entry point."""
        self._ensure_services()
        start = time.monotonic()

        # Stage 1-2: Connect & Collect
        source_status = self._get_data_source_status()
        raw_data = await self._collect_signals(db, org_id)

        total_signals = sum(1 for v in raw_data.values() if v and v != {})

        # Stage 3: Normalize
        normalization = await self._normalize(org_id, raw_data)
        signal_summary = await self._build_signal_summary(org_id, normalization)

        # Stage 4: Build Network
        network = await self._analyze_network(db, org_id)

        # Stage 5-6: Detect Patterns & Identify Risks
        risks = self._identify_risks(normalization, network, org_id)

        # Stage 7: Generate Explanations
        narrative = self._generate_narrative(risks, signal_summary, network)

        # Stage 8: Check Active Interventions
        active_interventions = await self._get_active_interventions(db, org_id)

        # Stage 9: Measure Improvement
        improvements = await self._measure_improvement(db, org_id)

        # Compute overall health
        health = self._compute_overall_health(signal_summary, network, risks)

        elapsed_ms = int((time.monotonic() - start) * 1000)

        risk_summary: Dict[str, int] = {}
        for r in risks:
            risk_summary[r.severity] = risk_summary.get(r.severity, 0) + 1

        result = IntelligenceCycleResult(
            org_id=org_id,
            cycle_timestamp=datetime.now(timezone.utc),
            cycle_duration_ms=elapsed_ms,
            data_sources=source_status,
            total_signals_collected=(
                normalization.signal_count if normalization else total_signals
            ),
            signal_summary=signal_summary,
            network_health=network.get("health_score", 0.0),
            network_signal_count=network.get("edge_count", 0),
            risks=risks,
            risk_summary=risk_summary,
            narrative_summary=narrative,
            active_interventions=active_interventions,
            improvement_metrics=improvements,
            overall_health_score=health,
        )

        logger.info(
            "Intelligence cycle completed for org=%s in %dms: "
            "signals=%d risks=%d health=%.1f",
            org_id,
            elapsed_ms,
            result.total_signals_collected,
            len(risks),
            health,
        )

        return result

    # ------------------------------------------------------------------
    # Stage 1-2: Connect & Collect
    # ------------------------------------------------------------------

    def _get_data_source_status(self) -> List[DataSourceStatus]:
        """Query DataSourceAggregator for connected data sources."""
        try:
            raw_status = self._aggregator.get_data_source_status()
        except Exception as exc:
            logger.warning("Failed to get data source status: %s", exc)
            return []

        result: List[DataSourceStatus] = []
        for name, info in raw_status.items():
            available = info.get("available", False)
            connector_count = info.get("connector_count", 0)

            if not available:
                health = "missing"
            elif connector_count > 0:
                health = "healthy"
            else:
                health = "stale"

            result.append(
                DataSourceStatus(
                    name=name,
                    connected=available,
                    signal_count=connector_count,
                    health=health,
                )
            )

        return result

    async def _collect_signals(self, db: AsyncSession, org_id: str) -> Dict[str, Any]:
        """Collect from all available data sources via DataSourceAggregator.

        Each gather call is wrapped in try/except so one failing source
        doesn't block the rest.
        """
        raw: Dict[str, Any] = {}

        # BI enrichment (calendar, work systems, HRIS, metadata)
        try:
            bi = await self._aggregator.gather_bi_enrichment(org_id)
            raw["bi_enrichment"] = bi
        except Exception as exc:
            logger.warning("BI enrichment collection failed: %s", exc)

        # Metadata burnout signals
        try:
            metadata = await self._aggregator.gather_metadata_burnout_signals(
                org_id, days=14
            )
            raw["metadata_burnout"] = metadata
        except Exception as exc:
            logger.warning("Metadata burnout collection failed: %s", exc)

        # ONA edges
        try:
            edges = await self._aggregator.gather_ona_edges(org_id)
            raw["ona_edges"] = edges
        except Exception as exc:
            logger.warning("ONA edge collection failed: %s", exc)

        # HRIS analysis
        try:
            hris = await self._aggregator.gather_hris_analysis(org_id)
            if hris:
                raw["hris"] = hris
        except Exception as exc:
            logger.warning("HRIS collection failed: %s", exc)

        # Pulse survey signals
        try:
            pulse = await self._aggregator.gather_pulse_survey_signals(
                db, org_id, lookback_days=30
            )
            if pulse:
                raw["pulse_survey"] = pulse
        except Exception as exc:
            logger.warning("Pulse survey collection failed: %s", exc)

        # Culture signals
        try:
            culture = await self._aggregator.gather_culture_signals(
                db, org_id, lookback_days=30
            )
            if culture:
                raw["culture"] = culture
        except Exception as exc:
            logger.warning("Culture signals collection failed: %s", exc)

        # Feedback signals
        try:
            feedback = await self._aggregator.gather_feedback_signals(
                db, org_id, lookback_days=90
            )
            if feedback:
                raw["feedback"] = feedback
        except Exception as exc:
            logger.warning("Feedback collection failed: %s", exc)

        # Recognition signals
        try:
            recognition = await self._aggregator.gather_recognition_signals(
                db, org_id, lookback_days=90
            )
            if recognition:
                raw["recognition"] = recognition
        except Exception as exc:
            logger.warning("Recognition collection failed: %s", exc)

        # Meeting effectiveness
        try:
            meetings = await self._aggregator.gather_meeting_signals(
                db, org_id, lookback_days=30
            )
            if meetings:
                raw["meeting_effectiveness"] = meetings
        except Exception as exc:
            logger.warning("Meeting signals collection failed: %s", exc)

        # 360 feedback
        try:
            fb360 = await self._aggregator.gather_360_feedback_signals(db, org_id)
            if fb360:
                raw["feedback_360"] = fb360
        except Exception as exc:
            logger.warning("360 feedback collection failed: %s", exc)

        # OKR signals
        try:
            okr = await self._aggregator.gather_okr_signals(db, org_id)
            if okr:
                raw["okr"] = okr
        except Exception as exc:
            logger.warning("OKR collection failed: %s", exc)

        # Toxicity signals
        try:
            toxicity = await self._aggregator.gather_toxicity_signals(org_id, days=30)
            if toxicity:
                raw["toxicity"] = toxicity
        except Exception as exc:
            logger.warning("Toxicity collection failed: %s", exc)

        # Passive burnout signals
        try:
            passive = await self._aggregator.gather_passive_burnout_signals(
                org_id, days=14
            )
            if passive:
                raw["passive_burnout"] = passive
        except Exception as exc:
            logger.warning("Passive burnout collection failed: %s", exc)

        # Project management signals
        try:
            pm = await self._aggregator.gather_project_management_signals(
                org_id, days=30
            )
            if pm:
                raw["project_management"] = pm
        except Exception as exc:
            logger.warning("Project management collection failed: %s", exc)

        # Lifecycle signals
        try:
            lifecycle = await self._aggregator.gather_lifecycle_signals(
                db, org_id, days=365
            )
            if lifecycle:
                raw["lifecycle"] = lifecycle
        except Exception as exc:
            logger.warning("Lifecycle collection failed: %s", exc)

        logger.info(
            "Intelligence loop collected %d data categories for org=%s",
            len(raw),
            org_id,
        )
        return raw

    # ------------------------------------------------------------------
    # Stage 3: Normalize
    # ------------------------------------------------------------------

    async def _normalize(self, org_id: str, raw_data: Dict[str, Any]):
        """Run through DataNormalizationService.

        Reshapes the aggregator output dict into the format the
        normalization layer expects (keyed by source type).
        """
        # Build the raw_data dict the normalization service expects
        norm_input: Dict[str, Any] = {}

        # Calendar / meeting data from BI enrichment
        bi = raw_data.get("bi_enrichment", {})
        if bi:
            if bi.get("meeting_health"):
                norm_input["calendar"] = bi["meeting_health"]
            elif bi.get("_sources") and "calendar" in bi.get("_sources", []):
                norm_input["calendar"] = {
                    "meeting_hours_per_week": bi.get("meeting_hours_per_week", 0),
                    "back_to_back_rate": bi.get("back_to_back_rate", 0),
                    "after_hours_ratio": bi.get("after_hours_ratio", 0),
                    "focus_hours_per_week": bi.get("focus_hours_per_week", 0),
                }

        # Work systems
        if bi.get("workload_snapshots"):
            norm_input["work_systems"] = bi["workload_snapshots"]

        # HRIS
        hris = raw_data.get("hris")
        if hris:
            norm_input["hris"] = hris

        # Metadata burnout
        metadata = raw_data.get("metadata_burnout")
        if metadata and metadata.get("_metadata_source_count", 0) > 0:
            norm_input["metadata_burnout"] = metadata

        # PTO from metadata
        if metadata and metadata.get("pto_patterns_burnout_risk") is not None:
            norm_input["pto"] = {
                "days_available": 20,  # default assumption
                "days_taken": max(
                    0, 20 - metadata.get("pto_patterns_burnout_risk", 0) / 5
                ),
                "cancellation_rate": 0,
                "days_since_last_vacation": 0,
            }

        # ONA edges
        ona_edges = raw_data.get("ona_edges", [])
        if ona_edges:
            norm_input["ona"] = {
                "total_edges": len(ona_edges),
                "cross_team_ratio": 0.3,  # placeholder -- real ONA computes this
            }

        # Toxicity composite into metadata burnout for wellbeing normalizer
        toxicity = raw_data.get("toxicity")
        if toxicity and toxicity.get("composite_toxicity_score") is not None:
            norm_input.setdefault("metadata_burnout", {})
            if "metadata_burnout_risk" not in norm_input["metadata_burnout"]:
                norm_input["metadata_burnout"]["metadata_burnout_risk"] = toxicity[
                    "composite_toxicity_score"
                ]

        try:
            return await self._normalization_service.normalize_all(
                org_id, norm_input, scope="organization"
            )
        except Exception as exc:
            logger.warning("Normalization failed for org=%s: %s", org_id, exc)
            return None

    async def _build_signal_summary(
        self, org_id: str, normalization
    ) -> Dict[str, float]:
        """Extract category -> avg score from NormalizationResult."""
        if normalization is None:
            return {}

        try:
            summary = await self._normalization_service.get_signal_summary(
                org_id, normalization.signals
            )
            # Flatten to category -> score
            return {
                k: v["score"]
                for k, v in summary.items()
                if isinstance(v, dict) and "score" in v and k != "overall"
            }
        except Exception as exc:
            logger.warning("Signal summary computation failed: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Stage 4: Network
    # ------------------------------------------------------------------

    async def _analyze_network(self, db: AsyncSession, org_id: str) -> Dict[str, Any]:
        """Run network analysis if the service is available.

        Uses NetworkIntelligenceEngine if present (being built concurrently),
        falls back to OrganizationalNetworkService, or returns empty dict.
        """
        # Try the new NetworkIntelligenceEngine first
        try:
            from app.services.network_intelligence import NetworkIntelligenceEngine

            engine = NetworkIntelligenceEngine()
            result = await engine.analyze(db, org_id)
            if result:
                return {
                    "health_score": result.get("network_health", 0),
                    "edge_count": result.get("edge_count", 0),
                    "isolated_nodes": result.get("isolated_nodes", []),
                    "bottleneck_nodes": result.get("bottleneck_nodes", []),
                    "communities": result.get("communities", []),
                }
        except (ImportError, AttributeError):
            pass
        except Exception as exc:
            logger.debug("NetworkIntelligenceEngine failed, trying ONA: %s", exc)

        # Fall back to existing OrganizationalNetworkService
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            result = await ona.analyze_organization(db, org_id)
            if result:
                insights = result.get("insights", {})
                return {
                    "health_score": result.get("network_health_score", 50.0),
                    "edge_count": result.get("edge_count", 0),
                    "isolated_nodes": insights.get("isolated", []),
                    "bottleneck_nodes": insights.get("bottlenecks", []),
                    "communities": result.get("communities", []),
                }
        except (ImportError, AttributeError):
            pass
        except Exception as exc:
            logger.debug("ONA service failed: %s", exc)

        return {"health_score": 0.0, "edge_count": 0}

    # ------------------------------------------------------------------
    # Stage 5-6: Detect Patterns & Identify Risks
    # ------------------------------------------------------------------

    def _identify_risks(
        self,
        normalization,
        network: Dict[str, Any],
        org_id: str,
    ) -> List[RiskCard]:
        """Convert normalized patterns + network signals into risk cards."""
        risks: List[RiskCard] = []
        seen_ids: set = set()

        # -- From normalization patterns --
        if normalization and normalization.patterns:
            for pattern in normalization.patterns:
                mapping = _PATTERN_RISK_MAP.get(pattern.pattern_type)
                risk_type = mapping[0] if mapping else pattern.pattern_type
                auto_action = mapping[1] if mapping else None
                title_template = (
                    mapping[2]
                    if mapping
                    else pattern.pattern_type.replace("_", " ").title()
                )

                rid = _risk_id(risk_type, pattern.scope, pattern.scope_id)
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)

                severity = _severity_label(pattern.severity)
                signals = [
                    {
                        "source": s.source,
                        "signal_type": s.signal_type,
                        "value": round(s.value, 1),
                        "confidence": round(s.confidence, 3),
                    }
                    for s in pattern.signals
                ]

                risks.append(
                    RiskCard(
                        risk_id=rid,
                        risk_type=risk_type,
                        severity=severity,
                        severity_score=round(pattern.severity, 1),
                        title=title_template,
                        explanation=pattern.description,
                        contributing_signals=signals,
                        affected_scope=pattern.scope,
                        affected_id=pattern.scope_id,
                        affected_name=f"Organization {org_id[:8]}",
                        recommendation=pattern.recommendation,
                        auto_action=auto_action if pattern.severity >= 55 else None,
                    )
                )

        # -- From network analysis --
        isolated = network.get("isolated_nodes", [])
        if isolated:
            rid = _risk_id("isolation", "organization", org_id)
            if rid not in seen_ids:
                seen_ids.add(rid)
                count = len(isolated)
                severity_score = min(100, count * 15)
                risks.append(
                    RiskCard(
                        risk_id=rid,
                        risk_type="isolation",
                        severity=_severity_label(severity_score),
                        severity_score=severity_score,
                        title=f"{count} employee{'s' if count != 1 else ''} isolated in the network",
                        explanation=(
                            f"{count} employee{'s have' if count != 1 else ' has'} "
                            f"few or no collaboration connections. "
                            f"Isolated employees are 3x more likely to leave within 6 months."
                        ),
                        contributing_signals=[
                            {
                                "source": "ona",
                                "signal_type": "network_isolation",
                                "value": severity_score,
                                "confidence": 0.8,
                            }
                        ],
                        affected_scope="organization",
                        affected_id=org_id,
                        affected_name=f"Organization {org_id[:8]}",
                        recommendation=(
                            "Assign collaboration buddies to isolated employees. "
                            "Include them in cross-functional projects. "
                            "Check in with their managers about workload and team integration."
                        ),
                        auto_action="collaboration" if severity_score >= 55 else None,
                    )
                )

        bottlenecks = network.get("bottleneck_nodes", [])
        if bottlenecks:
            rid = _risk_id("bottleneck", "organization", org_id)
            if rid not in seen_ids:
                seen_ids.add(rid)
                count = len(bottlenecks)
                severity_score = min(100, count * 20)
                risks.append(
                    RiskCard(
                        risk_id=rid,
                        risk_type="bottleneck",
                        severity=_severity_label(severity_score),
                        severity_score=severity_score,
                        title=f"{count} collaboration bottleneck{'s' if count != 1 else ''} detected",
                        explanation=(
                            f"{count} individual{'s are' if count != 1 else ' is'} acting as "
                            f"critical bridges between teams. "
                            f"If they leave or burn out, information flow will break down."
                        ),
                        contributing_signals=[
                            {
                                "source": "ona",
                                "signal_type": "network_bottleneck",
                                "value": severity_score,
                                "confidence": 0.75,
                            }
                        ],
                        affected_scope="organization",
                        affected_id=org_id,
                        affected_name=f"Organization {org_id[:8]}",
                        recommendation=(
                            "Distribute responsibilities held by bottleneck individuals. "
                            "Create redundant communication paths. "
                            "Document tribal knowledge they hold."
                        ),
                        auto_action="collaboration" if severity_score >= 55 else None,
                    )
                )

        # Sort by severity_score descending
        risks.sort(key=lambda r: r.severity_score, reverse=True)
        return risks

    # ------------------------------------------------------------------
    # Stage 7: Generate Explanations
    # ------------------------------------------------------------------

    def _generate_narrative(
        self,
        risks: List[RiskCard],
        signal_summary: Dict[str, float],
        network: Dict[str, Any],
    ) -> Optional[str]:
        """Generate 1-paragraph summary of the current state.

        Uses template-based generation -- no LLM required. If the
        NarrativeIntelligenceService is available and an LLM is configured,
        consumers can use that service separately for polished reports.
        """
        if not signal_summary and not risks:
            return "Insufficient data to generate a meaningful summary. Connect more data sources to enable intelligence analysis."

        parts: List[str] = []

        # Overall signal health
        if signal_summary:
            scores = list(signal_summary.values())
            avg = sum(scores) / len(scores)
            health_desc = (
                "healthy"
                if avg < 35
                else (
                    "showing moderate stress"
                    if avg < 55
                    else (
                        "under significant strain"
                        if avg < 75
                        else "in critical condition"
                    )
                )
            )
            parts.append(
                f"The organization is currently {health_desc} "
                f"across {len(signal_summary)} signal categories."
            )

            # Highlight worst category (highest score = worst, since signals
            # are on a 0-100 concern scale)
            if signal_summary:
                worst_cat = max(signal_summary, key=signal_summary.get)
                worst_score = signal_summary[worst_cat]
                if worst_score > 40:
                    parts.append(
                        f"The most concerning area is {worst_cat} "
                        f"(score: {worst_score:.0f}/100)."
                    )

        # Network health
        net_health = network.get("health_score", 0)
        if net_health > 0:
            if net_health >= 70:
                parts.append("Collaboration network is strong.")
            elif net_health >= 40:
                parts.append("Collaboration network shows some fragmentation.")
            else:
                parts.append("Collaboration network is fragmented and needs attention.")

        # Risk summary
        if risks:
            critical = sum(1 for r in risks if r.severity == "critical")
            high = sum(1 for r in risks if r.severity == "high")
            if critical > 0:
                parts.append(
                    f"{critical} critical risk{'s' if critical != 1 else ''} "
                    f"identified requiring immediate action."
                )
            elif high > 0:
                parts.append(
                    f"{high} high-severity risk{'s' if high != 1 else ''} "
                    f"detected that should be addressed this week."
                )
            else:
                parts.append(
                    f"{len(risks)} risk{'s' if len(risks) != 1 else ''} "
                    f"identified, none at critical severity."
                )

            # Top risk detail
            top = risks[0]
            parts.append(f"Top concern: {top.title}.")
        else:
            parts.append("No significant risks detected.")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Stage 8: Active Interventions
    # ------------------------------------------------------------------

    async def _get_active_interventions(self, db: AsyncSession, org_id: str) -> int:
        """Count active interventions/action plans."""
        try:
            from app.db.models.action_plan import ActionPlan, ActionPlanStatus

            result = await db.execute(
                select(func.count(ActionPlan.id)).where(
                    and_(
                        ActionPlan.organization_id == org_id,
                        ActionPlan.status.in_(
                            [
                                ActionPlanStatus.ACCEPTED.value,
                                ActionPlanStatus.IN_PROGRESS.value,
                            ]
                        ),
                    )
                )
            )
            return result.scalar_one_or_none() or 0
        except Exception as exc:
            logger.debug("Active intervention count failed: %s", exc)
            return 0

    # ------------------------------------------------------------------
    # Stage 9: Measure Improvement
    # ------------------------------------------------------------------

    async def _measure_improvement(
        self, db: AsyncSession, org_id: str
    ) -> List[ImprovementMetric]:
        """Compare current signals against intervention baselines."""
        try:
            from app.db.models.action_plan import ActionPlan, ActionPlanStatus

            # Query completed plans that have both before and after metrics
            result = await db.execute(
                select(ActionPlan).where(
                    and_(
                        ActionPlan.organization_id == org_id,
                        ActionPlan.status == ActionPlanStatus.COMPLETED.value,
                        ActionPlan.metric_before.isnot(None),
                        ActionPlan.metric_after.isnot(None),
                    )
                )
            )
            plans = list(result.scalars().all())

            if not plans:
                return []

            # Metrics where lower = better
            inverted = {"burnout_risk", "friction_index"}

            metrics: List[ImprovementMetric] = []
            for plan in plans:
                baseline = float(plan.metric_before)
                current = float(plan.metric_after)
                delta = current - baseline

                # For inverted metrics, improvement means the value went down
                effective_delta = -delta if plan.related_metric in inverted else delta

                if baseline != 0:
                    delta_pct = round((delta / baseline) * 100, 1)
                else:
                    delta_pct = 0.0

                if effective_delta > 2:
                    direction = "improving"
                elif effective_delta < -2:
                    direction = "worsening"
                else:
                    direction = "stable"

                metrics.append(
                    ImprovementMetric(
                        metric_name=plan.related_metric or "unknown",
                        baseline_value=baseline,
                        current_value=current,
                        delta=round(delta, 1),
                        delta_percent=delta_pct,
                        direction=direction,
                        intervention_id=str(plan.id),
                    )
                )

            return metrics

        except Exception as exc:
            logger.debug("Improvement measurement failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Overall Health Score
    # ------------------------------------------------------------------

    def _compute_overall_health(
        self,
        signal_summary: Dict[str, float],
        network: Dict[str, Any],
        risks: List[RiskCard],
    ) -> float:
        """Composite score: 100 = healthy, 0 = critical.

        Formula:
          base  = 100 - avg(signal scores)   [signals are concern-scale, so invert]
          network contributes 20% blend
          risk penalties: critical -15, high -8, medium -3
          clamp to [0, 100]
        """
        # Base from signal scores (inverted: low signal score = healthy)
        if signal_summary:
            avg_signal = sum(signal_summary.values()) / len(signal_summary)
            base = 100.0 - avg_signal
        else:
            base = 50.0  # neutral when no data

        # Blend network health at 20%
        net_health = network.get("health_score", 0)
        if net_health > 0:
            base = base * 0.8 + net_health * 0.2

        # Risk penalties
        penalties = {
            "critical": 15,
            "high": 8,
            "medium": 3,
            "low": 1,
        }
        total_penalty = sum(penalties.get(r.severity, 0) for r in risks)
        # Cap penalty at 60 to avoid negative health from many small risks
        total_penalty = min(60, total_penalty)

        health = base - total_penalty
        return round(max(0.0, min(100.0, health)), 1)

    # ------------------------------------------------------------------
    # Convenience: filtered views
    # ------------------------------------------------------------------

    async def get_risks(
        self,
        db: AsyncSession,
        org_id: str,
        severity: Optional[str] = None,
    ) -> List[RiskCard]:
        """Run cycle and return only risk cards, optionally filtered."""
        result = await self.run_cycle(db, org_id)
        if severity:
            return [r for r in result.risks if r.severity == severity]
        return result.risks

    async def get_health(self, db: AsyncSession, org_id: str) -> Dict[str, Any]:
        """Run cycle and return health score with breakdown."""
        result = await self.run_cycle(db, org_id)
        return {
            "overall_health_score": result.overall_health_score,
            "signal_summary": result.signal_summary,
            "network_health": result.network_health,
            "risk_summary": result.risk_summary,
            "active_interventions": result.active_interventions,
            "data_source_count": len([s for s in result.data_sources if s.connected]),
            "cycle_timestamp": result.cycle_timestamp.isoformat(),
        }

    async def get_improvements(
        self, db: AsyncSession, org_id: str
    ) -> List[ImprovementMetric]:
        """Run cycle and return improvement metrics."""
        result = await self.run_cycle(db, org_id)
        return result.improvement_metrics


# Module-level singleton
intelligence_loop = IntelligenceLoopOrchestrator()
