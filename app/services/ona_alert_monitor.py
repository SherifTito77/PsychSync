# app/services/ona_alert_monitor.py
"""
ONA Real-Time Alert Monitor

Compares consecutive NetworkSnapshots and triggers CommunicationAlerts
when organizational network metrics cross critical thresholds.

Designed to run as a scheduled background job (hourly or on new data).
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.communication_alerts import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    CommunicationAlert,
)
from app.db.models.network_analysis import NetworkSnapshot

logger = logging.getLogger(__name__)


# --- Threshold Configuration ---

DENSITY_DROP_WARNING = 0.15  # 15% relative drop triggers warning
DENSITY_DROP_CRITICAL = 0.25  # 25% relative drop triggers critical
ISOLATE_INCREASE_WARNING = 2  # 2+ new isolates triggers warning
ISOLATE_INCREASE_CRITICAL = 5  # 5+ new isolates triggers critical
BRIDGE_LOSS_WARNING = 1  # losing 1 bridge triggers warning
BRIDGE_LOSS_CRITICAL = 3  # losing 3+ bridges triggers critical
COMMUNITY_GROWTH_WARNING = 2  # 2+ new communities = fragmentation warning
COMMUNITY_GROWTH_CRITICAL = 4  # 4+ = critical fragmentation
DEDUP_WINDOW_HOURS = 24  # don't re-fire same alert type within this window


class ONAAlertMonitor:
    """Monitors ONA snapshots and generates threshold-based alerts."""

    async def check_organization(
        self, db: AsyncSession, org_id: UUID, lookback_days: int = 7
    ) -> list[dict[str, Any]]:
        """
        Compare latest snapshot against previous snapshot(s) for an org.
        Returns list of alert dicts created.
        """
        snapshots = await self._get_recent_snapshots(db, org_id, lookback_days)
        if len(snapshots) < 2:
            logger.info("org=%s: fewer than 2 snapshots, skipping alert check", org_id)
            return []

        current = snapshots[0]
        previous = snapshots[1]
        alerts_created = []

        # Run all threshold checks
        checks = [
            self._check_density_drop(current, previous, org_id),
            self._check_isolate_increase(current, previous, org_id),
            self._check_bridge_loss(current, previous, org_id),
            self._check_fragmentation(current, previous, org_id),
        ]

        for alert_data in checks:
            if alert_data is None:
                continue

            # Dedup: don't fire same alert type within window
            is_duplicate = await self._is_duplicate(
                db, org_id, alert_data["alert_type"], alert_data.get("team_id")
            )
            if is_duplicate:
                logger.debug(
                    "org=%s: suppressing duplicate %s alert",
                    org_id,
                    alert_data["alert_type"],
                )
                continue

            alert = await self._persist_alert(db, alert_data)
            alerts_created.append(alert_data)
            logger.info(
                "org=%s: created %s alert (severity=%s)",
                org_id,
                alert_data["alert_type"],
                alert_data["severity"],
            )

        await db.commit()
        return alerts_created

    async def check_all_organizations(
        self, db: AsyncSession, lookback_days: int = 7
    ) -> dict[str, list[dict]]:
        """Run alert checks across all orgs with recent snapshots."""
        result = await db.execute(
            select(NetworkSnapshot.organization_id)
            .distinct()
            .where(
                NetworkSnapshot.snapshot_date
                >= (datetime.now(timezone.utc) - timedelta(days=lookback_days)).date()
            )
        )
        org_ids = [row[0] for row in result.all()]

        all_alerts = {}
        for org_id in org_ids:
            alerts = await self.check_organization(db, org_id, lookback_days)
            if alerts:
                all_alerts[str(org_id)] = alerts

        return all_alerts

    # --- Threshold Checks ---

    def _check_density_drop(
        self, current: NetworkSnapshot, previous: NetworkSnapshot, org_id: UUID
    ) -> Optional[dict]:
        """Detect significant network density decline."""
        if not previous.density or float(previous.density) == 0:
            return None

        curr_density = float(current.density or 0)
        prev_density = float(previous.density)
        relative_drop = (prev_density - curr_density) / prev_density

        if relative_drop < DENSITY_DROP_WARNING:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if relative_drop >= DENSITY_DROP_CRITICAL
            else AlertSeverity.WARNING
        )

        return {
            "organization_id": org_id,
            "alert_type": AlertType.TEAM_FRAGMENTATION.value,
            "severity": severity.value,
            "title": f"Network density dropped {relative_drop:.0%}",
            "description": (
                f"Organizational network density declined from {prev_density:.4f} "
                f"to {curr_density:.4f} ({relative_drop:.0%} drop) between "
                f"{previous.snapshot_date} and {current.snapshot_date}. "
                f"This indicates weakening connections across the organization."
            ),
            "summary": f"Network density down {relative_drop:.0%} — connections weakening",
            "impact_description": (
                "Declining density reduces information flow, slows decision-making, "
                "and can lead to siloed teams."
            ),
            "detection_source": "ona_alert_monitor",
            "detection_confidence": min(0.6 + relative_drop, 0.95),
            "threshold_breached": {
                "metric": "network_density",
                "previous": prev_density,
                "current": curr_density,
                "relative_change": round(-relative_drop, 4),
                "threshold": DENSITY_DROP_WARNING,
            },
            "supporting_metrics": {
                "total_nodes_current": current.total_nodes,
                "total_edges_current": current.total_edges,
                "total_nodes_previous": previous.total_nodes,
                "total_edges_previous": previous.total_edges,
            },
            "recommended_actions": [
                "Review which teams lost connections",
                "Check for recent departures or team restructures",
                "Consider cross-team collaboration initiatives",
            ],
            "immediate_steps": [
                "Identify teams with the largest connectivity drop",
                "Schedule cross-team sync meetings",
            ],
            "impact_scope": "organization",
            "requires_immediate_attention": severity == AlertSeverity.CRITICAL,
            "time_to_resolve_hours": 72 if severity == AlertSeverity.CRITICAL else 168,
        }

    def _check_isolate_increase(
        self, current: NetworkSnapshot, previous: NetworkSnapshot, org_id: UUID
    ) -> Optional[dict]:
        """Detect new isolated employees."""
        curr_isolates = current.num_isolates or 0
        prev_isolates = previous.num_isolates or 0
        new_isolates = curr_isolates - prev_isolates

        if new_isolates < ISOLATE_INCREASE_WARNING:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if new_isolates >= ISOLATE_INCREASE_CRITICAL
            else AlertSeverity.WARNING
        )

        # Identify who became isolated by diffing node_metrics
        newly_isolated_ids = self._diff_isolates(current, previous)

        return {
            "organization_id": org_id,
            "alert_type": AlertType.COMMUNICATION_BREAKDOWN.value,
            "severity": severity.value,
            "title": f"{new_isolates} new isolated employee(s) detected",
            "description": (
                f"The number of isolated employees increased from {prev_isolates} "
                f"to {curr_isolates} (+{new_isolates}). Isolated employees have "
                f"minimal connections in the organizational network and may be "
                f"disengaged or at risk of departure."
            ),
            "summary": f"{new_isolates} employees became disconnected from the network",
            "impact_description": (
                "Isolated employees are 3x more likely to leave within 6 months. "
                "They also miss critical information and may underperform."
            ),
            "detection_source": "ona_alert_monitor",
            "detection_confidence": 0.85,
            "threshold_breached": {
                "metric": "num_isolates",
                "previous": prev_isolates,
                "current": curr_isolates,
                "change": new_isolates,
                "threshold": ISOLATE_INCREASE_WARNING,
            },
            "affected_users": newly_isolated_ids,
            "supporting_metrics": {
                "total_isolates": curr_isolates,
                "total_nodes": current.total_nodes,
                "isolation_rate": round(curr_isolates / max(current.total_nodes, 1), 3),
            },
            "recommended_actions": [
                "Reach out to newly isolated employees via their managers",
                "Assign cross-functional project work to rebuild connections",
                "Check if isolation correlates with recent team changes",
            ],
            "immediate_steps": [
                "Manager 1:1s with isolated employees within 48 hours",
                "Review if isolation is voluntary (remote preference) or involuntary",
            ],
            "impact_scope": "team",
            "requires_immediate_attention": severity == AlertSeverity.CRITICAL,
            "time_to_resolve_hours": 48 if severity == AlertSeverity.CRITICAL else 120,
        }

    def _check_bridge_loss(
        self, current: NetworkSnapshot, previous: NetworkSnapshot, org_id: UUID
    ) -> Optional[dict]:
        """Detect loss of bridge nodes (cross-team connectors)."""
        curr_bridges = current.num_bridges or 0
        prev_bridges = previous.num_bridges or 0
        lost_bridges = prev_bridges - curr_bridges

        if lost_bridges < BRIDGE_LOSS_WARNING:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if lost_bridges >= BRIDGE_LOSS_CRITICAL
            else AlertSeverity.WARNING
        )

        return {
            "organization_id": org_id,
            "alert_type": AlertType.COMMUNICATION_BREAKDOWN.value,
            "severity": severity.value,
            "title": f"{lost_bridges} cross-team bridge(s) lost",
            "description": (
                f"The organization lost {lost_bridges} bridge node(s) — people who "
                f"connected different teams/communities. Bridges dropped from "
                f"{prev_bridges} to {curr_bridges}. This weakens cross-team "
                f"information flow and collaboration."
            ),
            "summary": f"{lost_bridges} cross-team connectors lost — silos may form",
            "impact_description": (
                "Bridge loss is a leading indicator of team silos. Without "
                "connectors, teams operate in echo chambers and duplicate work."
            ),
            "detection_source": "ona_alert_monitor",
            "detection_confidence": 0.80,
            "threshold_breached": {
                "metric": "num_bridges",
                "previous": prev_bridges,
                "current": curr_bridges,
                "change": -lost_bridges,
                "threshold": BRIDGE_LOSS_WARNING,
            },
            "supporting_metrics": {
                "current_bridges": curr_bridges,
                "current_influencers": current.num_influencers or 0,
                "density": float(current.density or 0),
            },
            "recommended_actions": [
                "Identify which communities lost their bridge",
                "Create cross-team working groups or guilds",
                "Review if bridge loss correlates with departures or reorgs",
            ],
            "immediate_steps": [
                "Map which teams are now disconnected",
                "Assign temporary liaison roles between affected teams",
            ],
            "impact_scope": "organization",
            "requires_immediate_attention": severity == AlertSeverity.CRITICAL,
            "time_to_resolve_hours": 96,
        }

    def _check_fragmentation(
        self, current: NetworkSnapshot, previous: NetworkSnapshot, org_id: UUID
    ) -> Optional[dict]:
        """Detect organizational fragmentation (community count increase)."""
        curr_communities = current.num_communities or 0
        prev_communities = previous.num_communities or 0
        new_communities = curr_communities - prev_communities

        if new_communities < COMMUNITY_GROWTH_WARNING:
            return None

        severity = (
            AlertSeverity.CRITICAL
            if new_communities >= COMMUNITY_GROWTH_CRITICAL
            else AlertSeverity.WARNING
        )

        return {
            "organization_id": org_id,
            "alert_type": AlertType.TEAM_FRAGMENTATION.value,
            "severity": severity.value,
            "title": f"Organization fragmenting: {new_communities} new community clusters",
            "description": (
                f"Community count increased from {prev_communities} to "
                f"{curr_communities} (+{new_communities}). This indicates the "
                f"organization is splitting into more distinct groups, potentially "
                f"reducing cross-team collaboration and alignment."
            ),
            "summary": f"Org splitting into more silos ({prev_communities} → {curr_communities} communities)",
            "impact_description": (
                "Increasing fragmentation leads to duplicated efforts, "
                "misalignment on priorities, and cultural drift between groups."
            ),
            "detection_source": "ona_alert_monitor",
            "detection_confidence": 0.75,
            "threshold_breached": {
                "metric": "num_communities",
                "previous": prev_communities,
                "current": curr_communities,
                "change": new_communities,
                "threshold": COMMUNITY_GROWTH_WARNING,
            },
            "supporting_metrics": {
                "density": float(current.density or 0),
                "modularity": float(current.modularity_score or 0),
                "total_nodes": current.total_nodes,
            },
            "recommended_actions": [
                "Analyze which teams are separating",
                "Introduce cross-community rituals (all-hands, demos)",
                "Review communication channels for silos",
            ],
            "immediate_steps": [
                "Map the new community boundaries",
                "Identify if fragmentation aligns with org structure or is emergent",
            ],
            "impact_scope": "organization",
            "requires_immediate_attention": severity == AlertSeverity.CRITICAL,
            "time_to_resolve_hours": 168,
        }

    # --- Helpers ---

    def _diff_isolates(
        self, current: NetworkSnapshot, previous: NetworkSnapshot
    ) -> list[str]:
        """Find user IDs that became isolated between snapshots."""
        if not current.node_metrics or not previous.node_metrics:
            return []

        prev_connected = set()
        for node in previous.node_metrics or []:
            degree = node.get("degree", 0)
            if degree > 0:
                prev_connected.add(node.get("user_id", ""))

        newly_isolated = []
        for node in current.node_metrics or []:
            degree = node.get("degree", 0)
            uid = node.get("user_id", "")
            if degree == 0 and uid in prev_connected:
                newly_isolated.append(uid)

        return newly_isolated

    async def _get_recent_snapshots(
        self, db: AsyncSession, org_id: UUID, lookback_days: int
    ) -> list[NetworkSnapshot]:
        """Get the 2 most recent snapshots for an org."""
        result = await db.execute(
            select(NetworkSnapshot)
            .where(
                and_(
                    NetworkSnapshot.organization_id == org_id,
                    NetworkSnapshot.snapshot_date
                    >= (
                        datetime.now(timezone.utc) - timedelta(days=lookback_days)
                    ).date(),
                )
            )
            .order_by(desc(NetworkSnapshot.snapshot_date))
            .limit(2)
        )
        return list(result.scalars().all())

    async def _is_duplicate(
        self,
        db: AsyncSession,
        org_id: UUID,
        alert_type: str,
        team_id: Optional[UUID] = None,
    ) -> bool:
        """Check if a similar alert was already fired within the dedup window."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=DEDUP_WINDOW_HOURS)
        conditions = [
            CommunicationAlert.organization_id == org_id,
            CommunicationAlert.alert_type == alert_type,
            CommunicationAlert.detection_source == "ona_alert_monitor",
            CommunicationAlert.created_at >= cutoff,
            CommunicationAlert.status.in_(
                [AlertStatus.ACTIVE.value, AlertStatus.ACKNOWLEDGED.value]
            ),
        ]
        if team_id:
            conditions.append(CommunicationAlert.team_id == team_id)

        result = await db.execute(
            select(func.count())
            .select_from(CommunicationAlert)
            .where(and_(*conditions))
        )
        return result.scalar() > 0

    async def _persist_alert(
        self, db: AsyncSession, alert_data: dict
    ) -> CommunicationAlert:
        """Create a CommunicationAlert from alert data."""
        alert = CommunicationAlert(
            organization_id=alert_data["organization_id"],
            team_id=alert_data.get("team_id"),
            alert_type=alert_data["alert_type"],
            severity=alert_data["severity"],
            title=alert_data["title"],
            description=alert_data["description"],
            summary=alert_data.get("summary"),
            impact_description=alert_data.get("impact_description"),
            detected_at=datetime.now(timezone.utc),
            detection_source=alert_data.get("detection_source"),
            detection_confidence=alert_data.get("detection_confidence"),
            threshold_breached=alert_data.get("threshold_breached"),
            supporting_metrics=alert_data.get("supporting_metrics"),
            affected_users=alert_data.get("affected_users"),
            recommended_actions=alert_data.get("recommended_actions"),
            immediate_steps=alert_data.get("immediate_steps"),
            impact_scope=alert_data.get("impact_scope"),
            requires_immediate_attention=alert_data.get(
                "requires_immediate_attention", False
            ),
            time_to_resolve_hours=alert_data.get("time_to_resolve_hours"),
            auto_generated=True,
            detection_model="ona_alert_monitor",
            model_version="1.0",
            tags=["ona", "network_health"],
        )
        db.add(alert)
        return alert


# Singleton
ona_alert_monitor = ONAAlertMonitor()
