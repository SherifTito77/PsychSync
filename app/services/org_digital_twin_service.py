"""
Organizational Digital Twin Service

The living model of the organization.  Fuses 7 dimensions — teams,
managers, collaboration, performance, turnover risk, engagement, and
culture — into a single persistent, versioned snapshot that supports
temporal playback and what-if scenario simulation.

Data sources:
  - Team / TeamMember tables
  - BehavioralIntelligenceService (7 composite scores)
  - OrganizationalNetworkService (ONA: density, communities, manager dependency)
  - NetworkSnapshot (temporal network data)
  - CultureMetrics (psych safety, inclusivity, trust, innovation)
  - WellnessMetrics (engagement, burnout, resilience)
  - ChurnRiskScore (turnover prediction signals)
  - TeamRoleAnalysis (role effectiveness)
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base
from app.db.models.org_digital_twin import OrgDigitalTwinSnapshot
from app.db.models.team import Team, TeamMember

logger = logging.getLogger(__name__)

# Dimension weights for overall health score
_WEIGHTS = {
    "teams": 0.15,
    "managers": 0.10,
    "collaboration": 0.20,
    "performance": 0.10,
    "turnover_risk": 0.15,
    "engagement": 0.15,
    "culture": 0.15,
}


class OrganizationalDigitalTwinService:
    """
    Computes, persists, and simulates the organizational digital twin.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def get_current_twin(
        self,
        db: AsyncSession,
        organization_id: str,
        force_recompute: bool = False,
    ) -> Dict[str, Any]:
        """Return the latest twin snapshot, recomputing if stale or forced."""
        if not force_recompute:
            latest = await self._get_latest_snapshot(db, organization_id)
            if latest and self._is_fresh(latest):
                return self._snapshot_to_dict(latest)

        return await self.compute_twin_state(db, organization_id)

    async def compute_twin_state(
        self,
        db: AsyncSession,
        organization_id: str,
    ) -> Dict[str, Any]:
        """Full recomputation from all data sources.  Persists a new snapshot."""
        data_sources: Dict[str, bool] = {}

        # Compute all 7 dimensions
        teams_dim = await self._compute_teams(db, organization_id, data_sources)
        managers_dim = await self._compute_managers(db, organization_id, data_sources)
        collab_dim = await self._compute_collaboration(
            db, organization_id, data_sources
        )
        perf_dim = await self._compute_performance(db, organization_id, data_sources)
        turnover_dim = await self._compute_turnover_risk(
            db, organization_id, data_sources
        )
        engage_dim = await self._compute_engagement(db, organization_id, data_sources)
        culture_dim = await self._compute_culture(db, organization_id, data_sources)

        dimensions = {
            "teams": teams_dim,
            "managers": managers_dim,
            "collaboration": collab_dim,
            "performance": perf_dim,
            "turnover_risk": turnover_dim,
            "engagement": engage_dim,
            "culture": culture_dim,
        }

        # Overall health
        overall = sum(dimensions[k]["score"] * _WEIGHTS[k] for k in _WEIGHTS)

        # Determine trend from previous snapshot
        prev = await self._get_latest_snapshot(db, organization_id)
        trend = self._compute_trend(overall, prev)

        # Interconnection insights
        interconnections = self._compute_interconnections(dimensions)

        # Next version
        version = (prev.version + 1) if prev else 1

        # Persist snapshot
        snapshot = OrgDigitalTwinSnapshot(
            organization_id=organization_id,
            version=version,
            overall_health_score=round(overall, 1),
            overall_trend=trend,
            teams_score=round(teams_dim["score"], 1),
            managers_score=round(managers_dim["score"], 1),
            collaboration_score=round(collab_dim["score"], 1),
            performance_score=round(perf_dim["score"], 1),
            turnover_risk_score=round(turnover_dim["score"], 1),
            engagement_score=round(engage_dim["score"], 1),
            culture_score=round(culture_dim["score"], 1),
            state=dimensions,
            data_sources=data_sources,
        )
        db.add(snapshot)
        await db.commit()
        await db.refresh(snapshot)

        result = self._snapshot_to_dict(snapshot)
        result["interconnections"] = interconnections
        return result

    async def get_temporal_evolution(
        self,
        db: AsyncSession,
        organization_id: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Return recent snapshots for temporal playback."""
        query = (
            select(OrgDigitalTwinSnapshot)
            .where(
                and_(
                    OrgDigitalTwinSnapshot.organization_id == organization_id,
                    OrgDigitalTwinSnapshot.is_simulation.is_(False),
                )
            )
            .order_by(desc(OrgDigitalTwinSnapshot.computed_at))
            .limit(limit)
        )
        result = await db.execute(query)
        snapshots = result.scalars().all()
        return [self._snapshot_to_summary(s) for s in reversed(snapshots)]

    async def simulate_scenario(
        self,
        db: AsyncSession,
        organization_id: str,
        scenario: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a what-if scenario against the current twin state."""
        current = await self._get_latest_snapshot(db, organization_id)
        if not current:
            return {"error": "No twin state computed yet. Compute the twin first."}

        baseline = {
            "teams": current.teams_score,
            "managers": current.managers_score,
            "collaboration": current.collaboration_score,
            "performance": current.performance_score,
            "turnover_risk": current.turnover_risk_score,
            "engagement": current.engagement_score,
            "culture": current.culture_score,
            "overall": current.overall_health_score,
        }

        scenario_type = scenario.get("type", "")
        if scenario_type == "key_person_departure":
            predicted = await self._simulate_departure(
                db, organization_id, baseline, scenario
            )
        elif scenario_type == "team_merge":
            predicted = self._simulate_merge(baseline, scenario)
        elif scenario_type == "team_restructure":
            predicted = await self._simulate_restructure(
                db, organization_id, baseline, scenario
            )
        elif scenario_type == "engagement_shift":
            predicted = self._simulate_engagement_shift(baseline, scenario)
        elif scenario_type == "rapid_growth":
            predicted = self._simulate_growth(baseline, scenario)
        elif scenario_type == "hiring":
            predicted = await self._simulate_hiring(
                db, organization_id, baseline, scenario
            )
        else:
            return {"error": f"Unknown scenario type: {scenario_type}"}

        # Compute deltas
        deltas = {k: round(predicted[k] - baseline[k], 1) for k in baseline}

        # Recalculate overall
        predicted["overall"] = round(
            sum(predicted.get(k, baseline[k]) * _WEIGHTS.get(k, 0) for k in _WEIGHTS),
            1,
        )
        deltas["overall"] = round(predicted["overall"] - baseline["overall"], 1)

        # Determine if ONA data backed this simulation
        ona_backed = (
            scenario_type in ("key_person_departure", "team_restructure", "hiring")
            and scenario.get("person_id")
            or scenario.get("person_ids")
            or scenario.get("team_id")
        )

        # Risk narrative
        narrative = self._scenario_narrative(scenario_type, deltas)

        return {
            "scenario": scenario,
            "baseline": baseline,
            "predicted": predicted,
            "deltas": deltas,
            "risk_narrative": narrative,
            "confidence": self._scenario_confidence(scenario_type, bool(ona_backed)),
            "ona_backed": bool(ona_backed),
        }

    # ------------------------------------------------------------------
    # Dimension Computations
    # ------------------------------------------------------------------

    async def _compute_teams(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Teams dimension: team count, sizes, health from BI."""
        try:
            teams_q = select(Team).where(Team.organization_id == org_id)
            result = await db.execute(teams_q)
            teams = result.scalars().all()

            if not teams:
                sources["teams"] = False
                return self._empty_dimension("No teams found")

            sources["teams"] = True

            # Get member counts per team
            team_data = []
            total_members = 0
            for team in teams:
                members_q = (
                    select(func.count())
                    .select_from(TeamMember)
                    .where(TeamMember.team_id == team.id)
                )
                count_result = await db.execute(members_q)
                member_count = count_result.scalar() or 0
                total_members += member_count
                team_data.append(
                    {
                        "team_id": str(team.id),
                        "name": team.name,
                        "member_count": member_count,
                    }
                )

            avg_size = total_members / len(teams) if teams else 0
            # Score: penalize if teams too small (<3) or too large (>12)
            size_scores = []
            for t in team_data:
                mc = t["member_count"]
                if mc == 0:
                    size_scores.append(20)
                elif mc < 3:
                    size_scores.append(50)
                elif 3 <= mc <= 12:
                    size_scores.append(90)
                elif mc <= 20:
                    size_scores.append(70)
                else:
                    size_scores.append(50)

            # Try BI scores
            bi_score = await self._get_bi_team_health(db, org_id)

            team_structure_score = (
                sum(size_scores) / len(size_scores) if size_scores else 50
            )
            score = (
                team_structure_score * 0.4 + bi_score * 0.6
                if bi_score > 0
                else team_structure_score
            )

            return {
                "score": min(score, 100),
                "highlights": [
                    f"{len(teams)} teams, {total_members} total members",
                    f"Average team size: {avg_size:.1f}",
                ],
                "sub_metrics": {
                    "team_count": len(teams),
                    "total_members": total_members,
                    "avg_team_size": round(avg_size, 1),
                    "team_structure_score": round(team_structure_score, 1),
                    "bi_health_score": round(bi_score, 1),
                },
                "teams": team_data[:20],
            }
        except Exception as e:
            logger.warning("Teams dimension error: %s", e)
            sources["teams"] = False
            return self._empty_dimension(f"Error: {e}")

    async def _compute_managers(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Managers dimension: dependency ratios from ONA."""
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            network = await ona.analyze_organization(db, org_id)

            manager_dep = network.get("insights", {}).get("manager_dependency", {})
            if not manager_dep:
                sources["managers"] = False
                return self._empty_dimension(
                    "No ONA data — run collaboration surveys first"
                )

            sources["managers"] = True

            avg_dependency = manager_dep.get("avg_dependency_ratio", 0)
            high_risk_teams = manager_dep.get("high_risk_teams", [])
            bus_factor_risks = manager_dep.get("bus_factor_risks", [])

            # Score: low dependency = high score
            # dependency ratio 0 = ideal (100), >0.8 = critical (20)
            dep_score = max(0, 100 - avg_dependency * 100)

            bus_penalty = min(len(bus_factor_risks) * 10, 30)
            score = max(dep_score - bus_penalty, 10)

            highlights = [
                f"Avg manager dependency: {avg_dependency:.0%}",
            ]
            if high_risk_teams:
                highlights.append(
                    f"{len(high_risk_teams)} team(s) with high manager dependency"
                )
            if bus_factor_risks:
                highlights.append(
                    f"{len(bus_factor_risks)} bus-factor risk(s) detected"
                )

            return {
                "score": min(score, 100),
                "highlights": highlights,
                "sub_metrics": {
                    "avg_dependency_ratio": round(avg_dependency, 3),
                    "high_risk_teams": len(high_risk_teams),
                    "bus_factor_risks": len(bus_factor_risks),
                },
            }
        except Exception as e:
            logger.warning("Managers dimension error: %s", e)
            sources["managers"] = False
            return self._empty_dimension(f"Needs ONA data: {e}")

    async def _compute_collaboration(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Collaboration dimension: ONA density, communities, cross-team edges."""
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            network = await ona.analyze_organization(db, org_id)

            stats = network.get("network_stats", {})
            if stats.get("total_nodes", 0) == 0:
                sources["collaboration"] = False
                return self._empty_dimension("No network data")

            sources["collaboration"] = True

            density = stats.get("density", 0)
            num_communities = stats.get("num_communities", 0)
            cross_team = network.get("insights", {}).get("cross_team_collaboration", {})
            cross_team_score = cross_team.get("cross_team_density", 0)
            isolated_count = len(network.get("insights", {}).get("isolated", []))
            total_nodes = stats.get("total_nodes", 1)

            # Score: density (40%), cross-team (30%), isolation penalty (30%)
            density_score = min(density * 500, 100)  # 0.2 density = 100
            cross_score = min(cross_team_score * 200, 100)
            isolation_pct = isolated_count / total_nodes
            isolation_score = max(0, 100 - isolation_pct * 300)

            score = density_score * 0.4 + cross_score * 0.3 + isolation_score * 0.3

            return {
                "score": min(score, 100),
                "highlights": [
                    f"Network density: {density:.3f} ({total_nodes} people)",
                    f"{num_communities} communities detected",
                    f"{isolated_count} isolated employee(s)",
                ],
                "sub_metrics": {
                    "density": round(density, 4),
                    "num_communities": num_communities,
                    "cross_team_density": round(cross_team_score, 3),
                    "isolated_count": isolated_count,
                    "total_nodes": total_nodes,
                },
            }
        except Exception as e:
            logger.warning("Collaboration dimension error: %s", e)
            sources["collaboration"] = False
            return self._empty_dimension(f"Needs ONA data: {e}")

    async def _compute_performance(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Performance dimension: role effectiveness + OKR achievement."""
        try:
            from app.db.models.team_dynamics import TeamRoleAnalysis

            # --- Role analysis signal ---
            query = select(
                func.avg(TeamRoleAnalysis.role_effectiveness_score),
                func.avg(TeamRoleAnalysis.role_fit_score),
                func.count(),
            ).where(TeamRoleAnalysis.organization_id == org_id)
            result = await db.execute(query)
            row = result.one_or_none()

            has_roles = row and row[2] > 0
            avg_effectiveness = float(row[0] or 50) if has_roles else 50
            avg_fit = float(row[1] or 50) if has_roles else 50
            role_count = row[2] if has_roles else 0
            role_score = avg_effectiveness * 0.6 + avg_fit * 0.4

            # --- OKR achievement signal ---
            okr_score, okr_metrics = await self._compute_okr_signal(db, org_id)

            sources["performance"] = (
                has_roles or okr_metrics.get("total_objectives", 0) > 0
            )

            if not sources["performance"]:
                return self._empty_dimension(
                    "No role analysis or OKR data — complete assessments or set objectives"
                )

            # Blend: when both signals present, OKR gets 40% (outcome data is concrete)
            if has_roles and okr_score is not None:
                score = role_score * 0.60 + okr_score * 0.40
            elif okr_score is not None:
                score = okr_score
            else:
                score = role_score

            highlights = []
            if has_roles:
                highlights.append(
                    f"Avg role effectiveness: {avg_effectiveness:.0f}/100"
                )
                highlights.append(f"Avg role fit: {avg_fit:.0f}/100")
            if okr_metrics.get("total_objectives", 0) > 0:
                highlights.append(
                    f"OKR completion: {okr_metrics['completion_rate']:.0f}% "
                    f"({okr_metrics['completed_objectives']}/{okr_metrics['total_objectives']} objectives)"
                )
                if okr_metrics.get("at_risk_krs", 0) > 0:
                    highlights.append(
                        f"{okr_metrics['at_risk_krs']} key results at risk or off track"
                    )

            sub_metrics = {
                "avg_effectiveness": round(avg_effectiveness, 1),
                "avg_role_fit": round(avg_fit, 1),
                "analyses_count": role_count,
            }
            sub_metrics.update(okr_metrics)

            return {
                "score": min(score, 100),
                "highlights": highlights,
                "sub_metrics": sub_metrics,
            }
        except Exception as e:
            logger.warning("Performance dimension error: %s", e)
            sources["performance"] = False
            return self._empty_dimension(f"Error: {e}")

    async def _compute_okr_signal(self, db: AsyncSession, org_id: str) -> tuple:
        """Extract OKR health as a 0-100 performance signal."""
        try:
            from app.db.models.okr import Objective, KeyResult, OKRStatus, KRStatus

            # Active + completed objectives for this org
            obj_result = await db.execute(
                select(
                    func.count(),
                    func.count().filter(Objective.status == OKRStatus.COMPLETED),
                    func.avg(Objective.progress_percentage),
                ).where(
                    Objective.organization_id == org_id,
                    Objective.status.in_([OKRStatus.ACTIVE, OKRStatus.COMPLETED]),
                )
            )
            obj_row = obj_result.one()
            total_obj = obj_row[0] or 0
            completed_obj = obj_row[1] or 0
            avg_progress = float(obj_row[2] or 0)

            if total_obj == 0:
                return None, {"total_objectives": 0}

            # Key result health breakdown
            kr_result = await db.execute(
                select(
                    func.count(),
                    func.count().filter(KeyResult.status == KRStatus.ACHIEVED),
                    func.count().filter(
                        KeyResult.status.in_([KRStatus.AT_RISK, KRStatus.OFF_TRACK])
                    ),
                ).where(
                    KeyResult.objective_id.in_(
                        select(Objective.id).where(
                            Objective.organization_id == org_id,
                            Objective.status.in_(
                                [OKRStatus.ACTIVE, OKRStatus.COMPLETED]
                            ),
                        )
                    )
                )
            )
            kr_row = kr_result.one()
            total_krs = kr_row[0] or 0
            achieved_krs = kr_row[1] or 0
            at_risk_krs = kr_row[2] or 0

            # Score: blend completion rate + avg progress + KR health
            completion_rate = (completed_obj / total_obj) * 100 if total_obj else 0
            kr_achievement = (achieved_krs / total_krs) * 100 if total_krs else 0
            kr_risk_penalty = (at_risk_krs / max(total_krs, 1)) * 30

            okr_score = (
                avg_progress * 0.40 + completion_rate * 0.30 + kr_achievement * 0.30
            ) - kr_risk_penalty
            okr_score = max(0, min(100, okr_score))

            metrics = {
                "total_objectives": total_obj,
                "completed_objectives": completed_obj,
                "completion_rate": round(completion_rate, 1),
                "avg_objective_progress": round(avg_progress, 1),
                "total_krs": total_krs,
                "achieved_krs": achieved_krs,
                "at_risk_krs": at_risk_krs,
                "kr_achievement_rate": round(kr_achievement, 1),
            }
            return okr_score, metrics

        except Exception as e:
            logger.debug("OKR signal unavailable: %s", e)
            return None, {"total_objectives": 0}

    async def _compute_turnover_risk(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Turnover risk dimension: churn scores + BI burnout."""
        try:
            from app.db.models.churn_prediction import ChurnRiskScore
            from app.db.models.wellness_burnout import WellnessMetrics

            # Average churn risk
            churn_q = (
                select(
                    func.avg(ChurnRiskScore.overall_score),
                    func.count(),
                    func.count().filter(
                        ChurnRiskScore.overall_risk.in_(["high", "critical"])
                    ),
                )
                .join(
                    TeamMember,
                    TeamMember.user_id == ChurnRiskScore.user_id,
                )
                .join(Team, Team.id == TeamMember.team_id)
                .where(Team.organization_id == org_id)
            )
            churn_result = await db.execute(churn_q)
            churn_row = churn_result.one_or_none()

            # Burnout risk from wellness
            burnout_q = (
                select(func.avg(WellnessMetrics.burnout_risk_score))
                .where(WellnessMetrics.organization_id == org_id)
                .where(
                    WellnessMetrics.measurement_date
                    >= date.today() - timedelta(days=90)
                )
            )
            burnout_result = await db.execute(burnout_q)
            avg_burnout = burnout_result.scalar()

            has_churn = churn_row and churn_row[1] > 0
            has_burnout = avg_burnout is not None

            if not has_churn and not has_burnout:
                sources["turnover_risk"] = False
                return self._empty_dimension("No churn or burnout data")

            sources["turnover_risk"] = True

            # Invert: high risk = low score
            churn_avg = float(churn_row[0] or 0) if has_churn else 0
            high_risk_count = churn_row[2] if has_churn else 0
            total_scored = churn_row[1] if has_churn else 0

            # Burnout is 0-10 scale, map to 0-100
            burnout_pct = float(avg_burnout or 0) * 10 if has_burnout else 0

            if has_churn and has_burnout:
                risk = churn_avg * 0.6 + burnout_pct * 0.4
            elif has_churn:
                risk = churn_avg
            else:
                risk = burnout_pct

            score = max(0, 100 - risk)

            highlights = []
            if has_churn:
                highlights.append(
                    f"Avg churn risk: {churn_avg:.0f}/100 ({total_scored} scored)"
                )
                if high_risk_count:
                    highlights.append(
                        f"{high_risk_count} high/critical risk employee(s)"
                    )
            if has_burnout:
                highlights.append(f"Avg burnout risk: {burnout_pct:.0f}/100")

            return {
                "score": min(score, 100),
                "highlights": highlights,
                "sub_metrics": {
                    "avg_churn_risk": round(churn_avg, 1),
                    "high_risk_count": high_risk_count,
                    "avg_burnout_risk": round(burnout_pct, 1),
                    "composite_risk": round(risk, 1),
                },
            }
        except Exception as e:
            logger.warning("Turnover risk dimension error: %s", e)
            sources["turnover_risk"] = False
            return self._empty_dimension(f"Error: {e}")

    async def _compute_engagement(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Engagement dimension: wellness + culture + peer recognition."""
        try:
            from app.db.models.culture_metrics import CultureMetrics
            from app.db.models.wellness_burnout import WellnessMetrics

            # Wellness engagement (0-10 scale)
            wellness_q = (
                select(
                    func.avg(WellnessMetrics.engagement_level),
                    func.avg(WellnessMetrics.overall_wellness_score),
                    func.count(),
                )
                .where(WellnessMetrics.organization_id == org_id)
                .where(
                    WellnessMetrics.measurement_date
                    >= date.today() - timedelta(days=90)
                )
            )
            w_result = await db.execute(wellness_q)
            w_row = w_result.one_or_none()

            # Culture engagement (0-100 scale)
            culture_q = select(
                func.avg(CultureMetrics.engagement_level),
                func.avg(CultureMetrics.overall_morale_score),
                func.avg(CultureMetrics.enthusiasm_indicators),
            ).where(CultureMetrics.organization_id == org_id)
            c_result = await db.execute(culture_q)
            c_row = c_result.one_or_none()

            # Peer recognition signal
            rec_score, rec_metrics = await self._compute_recognition_signal(db, org_id)

            has_wellness = w_row and w_row[2] > 0
            has_culture = c_row and c_row[0] is not None
            has_recognition = rec_score is not None

            if not has_wellness and not has_culture and not has_recognition:
                sources["engagement"] = False
                return self._empty_dimension("No engagement data")

            sources["engagement"] = True

            # Normalize: wellness is 0-10 → 0-100, culture is already 0-100
            w_engage = float(w_row[0] or 0) * 10 if has_wellness else 0
            w_wellness = float(w_row[1] or 0) * 10 if has_wellness else 0
            c_engage = float(c_row[0] or 0) if has_culture else 0
            c_morale = float(c_row[1] or 0) if has_culture else 0

            # Adaptive blending: recognition gets 15% when available
            if has_wellness and has_culture and has_recognition:
                score = (
                    w_engage * 0.25
                    + w_wellness * 0.18
                    + c_engage * 0.25
                    + c_morale * 0.17
                    + rec_score * 0.15
                )
            elif has_wellness and has_culture:
                score = (
                    w_engage * 0.3 + w_wellness * 0.2 + c_engage * 0.3 + c_morale * 0.2
                )
            elif has_wellness and has_recognition:
                score = w_engage * 0.45 + w_wellness * 0.35 + rec_score * 0.20
            elif has_culture and has_recognition:
                score = c_engage * 0.45 + c_morale * 0.35 + rec_score * 0.20
            elif has_wellness:
                score = w_engage * 0.6 + w_wellness * 0.4
            elif has_recognition:
                score = rec_score
            else:
                score = c_engage * 0.6 + c_morale * 0.4

            highlights = []
            if has_wellness:
                highlights.append(
                    f"Wellness engagement: {w_engage:.0f}/100 ({w_row[2]} records)"
                )
            if has_culture:
                highlights.append(f"Culture engagement: {c_engage:.0f}/100")
                highlights.append(f"Morale: {c_morale:.0f}/100")
            if has_recognition:
                highlights.append(
                    f"Recognition activity: {rec_metrics['total_recognitions']} events "
                    f"({rec_metrics['unique_recognizers']} givers, "
                    f"{rec_metrics['unique_recipients']} receivers)"
                )

            sub_metrics = {
                "wellness_engagement": round(w_engage, 1),
                "wellness_score": round(w_wellness, 1),
                "culture_engagement": round(c_engage, 1),
                "morale": round(c_morale, 1),
            }
            sub_metrics.update(rec_metrics)

            return {
                "score": min(score, 100),
                "highlights": highlights,
                "sub_metrics": sub_metrics,
            }
        except Exception as e:
            logger.warning("Engagement dimension error: %s", e)
            sources["engagement"] = False
            return self._empty_dimension(f"Error: {e}")

    async def _compute_recognition_signal(self, db: AsyncSession, org_id: str) -> tuple:
        """Extract peer recognition density as an engagement signal (0-100)."""
        try:
            from app.db.models.peer_recognition import PeerRecognition

            since = datetime.utcnow() - timedelta(days=90)

            result = await db.execute(
                select(
                    func.count(),
                    func.count(func.distinct(PeerRecognition.recognizer_id)),
                    func.count(func.distinct(PeerRecognition.recipient_id)),
                ).where(
                    PeerRecognition.organization_id == org_id,
                    PeerRecognition.created_at >= since,
                )
            )
            row = result.one()
            total = row[0] or 0
            unique_givers = row[1] or 0
            unique_receivers = row[2] or 0

            metrics = {
                "total_recognitions": total,
                "unique_recognizers": unique_givers,
                "unique_recipients": unique_receivers,
            }

            if total == 0:
                return None, metrics

            # Score: recognition frequency + breadth of participation
            # 50+ recognitions/quarter = healthy org, 10+ unique givers = broad participation
            frequency_signal = min(100, (total / 50) * 100)
            breadth_signal = min(100, (unique_givers / max(10, unique_receivers)) * 100)
            # Ratio of receivers to givers — close to 1.0 means recognition flows both ways
            reciprocity = min(unique_receivers, unique_givers) / max(
                unique_receivers, unique_givers, 1
            )
            reciprocity_signal = reciprocity * 100

            score = (
                frequency_signal * 0.40
                + breadth_signal * 0.35
                + reciprocity_signal * 0.25
            )
            metrics["recognition_score"] = round(score, 1)
            return min(100, score), metrics

        except Exception as e:
            logger.debug("Recognition signal unavailable: %s", e)
            return None, {
                "total_recognitions": 0,
                "unique_recognizers": 0,
                "unique_recipients": 0,
            }

    async def _compute_culture(
        self, db: AsyncSession, org_id: str, sources: Dict
    ) -> Dict[str, Any]:
        """Culture dimension: CultureMetrics comprehensive model."""
        try:
            from app.db.models.culture_metrics import CultureMetrics

            query = select(
                func.avg(CultureMetrics.psychological_safety_score),
                func.avg(CultureMetrics.inclusivity_score),
                func.avg(CultureMetrics.transparency_score),
                func.avg(CultureMetrics.collaboration_effectiveness),
                func.avg(CultureMetrics.innovation_culture),
                func.avg(CultureMetrics.work_life_balance_score),
                func.count(),
            ).where(CultureMetrics.organization_id == org_id)
            result = await db.execute(query)
            row = result.one_or_none()

            if not row or row[6] == 0:
                sources["culture"] = False
                return self._empty_dimension("No culture metrics data")

            sources["culture"] = True

            psych_safety = float(row[0] or 0)
            inclusivity = float(row[1] or 0)
            transparency = float(row[2] or 0)
            collaboration = float(row[3] or 0)
            innovation = float(row[4] or 0)
            work_life = float(row[5] or 0)

            score = (
                psych_safety * 0.25
                + inclusivity * 0.15
                + transparency * 0.15
                + collaboration * 0.20
                + innovation * 0.10
                + work_life * 0.15
            )

            return {
                "score": min(score, 100),
                "highlights": [
                    f"Psychological safety: {psych_safety:.0f}/100",
                    f"Collaboration effectiveness: {collaboration:.0f}/100",
                    f"Innovation culture: {innovation:.0f}/100",
                ],
                "sub_metrics": {
                    "psychological_safety": round(psych_safety, 1),
                    "inclusivity": round(inclusivity, 1),
                    "transparency": round(transparency, 1),
                    "collaboration": round(collaboration, 1),
                    "innovation": round(innovation, 1),
                    "work_life_balance": round(work_life, 1),
                },
            }
        except Exception as e:
            logger.warning("Culture dimension error: %s", e)
            sources["culture"] = False
            return self._empty_dimension(f"Error: {e}")

    # ------------------------------------------------------------------
    # What-If Simulations
    # ------------------------------------------------------------------

    async def _simulate_departure(
        self,
        db: AsyncSession,
        org_id: str,
        baseline: Dict,
        scenario: Dict,
    ) -> Dict[str, float]:
        """Simulate a key person leaving — person-specific if person_id given.

        When person_id is provided, queries ONA for their actual centrality,
        bridging score, and role. Impact scales with their real network position:
        - betweenness_centrality: how many communication paths they carry
        - bridging_score: cross-team connectivity they provide
        - degree_centrality: direct relationships that break
        """
        predicted = dict(baseline)
        person_id = scenario.get("person_id")
        ona_profile = None

        if person_id:
            ona_profile = await self._get_person_ona_profile(db, org_id, person_id)

        if ona_profile:
            # Person-specific impact from real ONA data
            bc = ona_profile["betweenness_centrality"]
            dc = ona_profile["degree_centrality"]
            bs = ona_profile["bridging_score"]
            role = ona_profile["role"]

            # Scale factors: centrality normalized to impact magnitude
            # A person with bc=0.3 is ~6x more impactful than bc=0.05
            collab_impact = max(bc * 80, 5) + bs * 15
            team_impact = bs * 25 + dc * 10
            engagement_impact = dc * 20 + bc * 15

            predicted["collaboration"] = max(
                baseline["collaboration"] - collab_impact, 5
            )
            predicted["teams"] = max(baseline["teams"] - team_impact, 5)
            predicted["engagement"] = max(baseline["engagement"] - engagement_impact, 5)

            # Role-specific additional effects
            if role == "influencer":
                predicted["culture"] = max(baseline["culture"] - (bc * 40 + 5), 5)
            elif role == "bridge":
                # Bridges hold communities together
                predicted["collaboration"] -= min(bs * 10, 10)
                predicted["collaboration"] = max(predicted["collaboration"], 5)
            elif role in ("manager", "connector"):
                predicted["managers"] = max(baseline["managers"] - (dc * 30 + 5), 5)
                predicted["turnover_risk"] = max(baseline["turnover_risk"] - 10, 5)
        else:
            # Fallback: role-based static deltas (original behavior)
            role = scenario.get("role", "manager")
            if role == "manager":
                predicted["managers"] = max(baseline["managers"] - 20, 5)
                predicted["teams"] = max(baseline["teams"] - 10, 5)
                predicted["engagement"] = max(baseline["engagement"] - 12, 5)
                predicted["turnover_risk"] = max(baseline["turnover_risk"] - 15, 5)
                predicted["culture"] = max(baseline["culture"] - 8, 5)
            elif role == "influencer":
                predicted["collaboration"] = max(baseline["collaboration"] - 25, 5)
                predicted["engagement"] = max(baseline["engagement"] - 10, 5)
                predicted["culture"] = max(baseline["culture"] - 12, 5)
            elif role == "bridge":
                predicted["collaboration"] = max(baseline["collaboration"] - 20, 5)
                predicted["teams"] = max(baseline["teams"] - 8, 5)
            else:
                predicted["teams"] = max(baseline["teams"] - 5, 5)
                predicted["turnover_risk"] = max(baseline["turnover_risk"] - 3, 5)

        return predicted

    async def _get_person_ona_profile(
        self, db: AsyncSession, org_id: str, person_id: str
    ) -> Optional[Dict[str, Any]]:
        """Query ONA for a specific person's network metrics."""
        try:
            from app.services.organizational_network_service import (
                OrganizationalNetworkService,
            )

            ona = OrganizationalNetworkService()
            network = await ona.analyze_organization(db, org_id)
            for node in network.get("nodes", []):
                if node["user_id"] == person_id:
                    return node
        except Exception as e:
            logger.warning("ONA lookup failed for person %s: %s", person_id, e)
        return None

    async def _simulate_restructure(
        self,
        db: AsyncSession,
        org_id: str,
        baseline: Dict,
        scenario: Dict,
    ) -> Dict[str, float]:
        """Simulate moving person(s) between teams.

        Uses ONA cross-team edge density to predict collaboration disruption.
        Moving a bridge between teams has very different impact than moving
        an isolated node.
        """
        predicted = dict(baseline)
        person_ids = scenario.get("person_ids", [])
        target_team = scenario.get("target_team_id")

        if not person_ids or not target_team:
            # Generic restructure — moderate disruption
            predicted["culture"] = max(baseline["culture"] - 10, 5)
            predicted["collaboration"] = max(baseline["collaboration"] - 8, 5)
            predicted["teams"] = max(baseline["teams"] - 5, 5)
            return predicted

        total_bridge_score = 0.0
        total_centrality = 0.0

        for pid in person_ids:
            profile = await self._get_person_ona_profile(db, org_id, pid)
            if profile:
                total_bridge_score += profile["bridging_score"]
                total_centrality += profile["betweenness_centrality"]

        # Moving bridges disrupts cross-team communication
        collab_impact = total_bridge_score * 20 + 3
        culture_impact = total_centrality * 15 + 5
        # But restructuring can improve team structure
        team_upside = min(len(person_ids) * 2, 8)

        predicted["collaboration"] = max(baseline["collaboration"] - collab_impact, 5)
        predicted["culture"] = max(baseline["culture"] - culture_impact, 5)
        predicted["teams"] = min(baseline["teams"] + team_upside, 100)
        predicted["engagement"] = max(
            baseline["engagement"] - (culture_impact * 0.3), 5
        )

        return predicted

    async def _simulate_hiring(
        self,
        db: AsyncSession,
        org_id: str,
        baseline: Dict,
        scenario: Dict,
    ) -> Dict[str, float]:
        """Simulate hiring into a specific team.

        Predicts density dilution (new hires aren't connected yet) and
        capacity boost. Larger teams absorb hires better.
        """
        predicted = dict(baseline)
        team_id = scenario.get("team_id")
        hire_count = scenario.get("hire_count", 1)

        # Get current team size for dilution calculation
        current_size = 0
        if team_id:
            result = await db.execute(
                select(func.count())
                .select_from(TeamMember)
                .where(TeamMember.team_id == team_id)
            )
            current_size = result.scalar() or 0

        if current_size == 0:
            current_size = 10  # fallback assumption

        # Dilution: new hires aren't connected — density drops
        # Impact inversely proportional to team size (large teams absorb better)
        dilution_ratio = hire_count / (current_size + hire_count)
        collab_dilution = dilution_ratio * 25
        culture_dilution = dilution_ratio * 20

        predicted["collaboration"] = max(baseline["collaboration"] - collab_dilution, 5)
        predicted["culture"] = max(baseline["culture"] - culture_dilution, 5)
        # But capacity improves performance potential
        capacity_boost = min(hire_count * 3, 15)
        predicted["performance"] = min(baseline["performance"] + capacity_boost, 100)
        # Manager load increases
        if hire_count > 3:
            predicted["managers"] = max(baseline["managers"] - (hire_count - 3) * 2, 5)

        return predicted

    def _simulate_merge(self, baseline: Dict, scenario: Dict) -> Dict[str, float]:
        """Simulate merging two teams."""
        predicted = dict(baseline)
        # Merges create short-term culture disruption, collaboration friction
        predicted["culture"] = max(baseline["culture"] - 15, 5)
        predicted["collaboration"] = max(baseline["collaboration"] - 10, 5)
        predicted["engagement"] = max(baseline["engagement"] - 8, 5)
        predicted["managers"] = max(baseline["managers"] - 5, 5)
        # But can improve team structure and performance long-term
        predicted["teams"] = min(baseline["teams"] + 5, 100)
        return predicted

    def _simulate_engagement_shift(
        self, baseline: Dict, scenario: Dict
    ) -> Dict[str, float]:
        """Simulate engagement changing by X%."""
        predicted = dict(baseline)
        shift = scenario.get("shift_pct", -10)
        predicted["engagement"] = max(min(baseline["engagement"] + shift, 100), 5)
        # Cascading effects
        cascade = shift * 0.5
        predicted["turnover_risk"] = max(
            min(baseline["turnover_risk"] + cascade, 100), 5
        )
        predicted["culture"] = max(min(baseline["culture"] + cascade * 0.6, 100), 5)
        predicted["performance"] = max(
            min(baseline["performance"] + cascade * 0.4, 100), 5
        )
        return predicted

    def _simulate_growth(self, baseline: Dict, scenario: Dict) -> Dict[str, float]:
        """Simulate rapid headcount growth."""
        predicted = dict(baseline)
        growth_pct = scenario.get("growth_pct", 30)
        dilution = min(growth_pct * 0.5, 30)

        predicted["culture"] = max(baseline["culture"] - dilution, 5)
        predicted["collaboration"] = max(baseline["collaboration"] - dilution * 0.8, 5)
        predicted["managers"] = max(baseline["managers"] - dilution * 0.6, 5)
        predicted["engagement"] = max(baseline["engagement"] - dilution * 0.3, 5)
        predicted["teams"] = min(baseline["teams"] + 5, 100)
        return predicted

    def _scenario_narrative(self, scenario_type: str, deltas: Dict) -> str:
        """Generate human-readable impact narrative."""
        worst = min(deltas.items(), key=lambda x: x[1])
        best = max(
            ((k, v) for k, v in deltas.items() if k != "overall"),
            key=lambda x: x[1],
        )

        label = {
            "key_person_departure": "key person departure",
            "team_merge": "team merger",
            "team_restructure": "team restructure",
            "engagement_shift": "engagement shift",
            "rapid_growth": "rapid growth",
            "hiring": "new hire integration",
        }.get(scenario_type, scenario_type)

        parts = [
            f"A {label} scenario predicts an overall health change of "
            f"{deltas['overall']:+.1f} points."
        ]

        if worst[1] < -5:
            parts.append(
                f"Highest impact: {worst[0].replace('_', ' ')} "
                f"({worst[1]:+.1f} points)."
            )

        if best[1] > 0:
            parts.append(
                f"Potential upside: {best[0].replace('_', ' ')} "
                f"({best[1]:+.1f} points)."
            )

        return " ".join(parts)

    def _scenario_confidence(
        self, scenario_type: str, ona_backed: bool = False
    ) -> float:
        """Return confidence level (0-1) for simulation accuracy."""
        base = {
            "key_person_departure": 0.65,
            "team_merge": 0.55,
            "team_restructure": 0.60,
            "engagement_shift": 0.70,
            "rapid_growth": 0.60,
            "hiring": 0.55,
        }.get(scenario_type, 0.50)
        # ONA-backed simulations get a confidence boost
        if ona_backed:
            base = min(base + 0.15, 0.95)
        return base

    # ------------------------------------------------------------------
    # Interconnection Analysis
    # ------------------------------------------------------------------

    def _compute_interconnections(self, dims: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Detect notable relationships between dimensions."""
        insights = []

        scores = {k: v["score"] for k, v in dims.items()}

        # High burnout + low engagement = retention crisis
        if scores["turnover_risk"] < 40 and scores["engagement"] < 50:
            insights.append(
                {
                    "type": "crisis_signal",
                    "dimensions": ["turnover_risk", "engagement"],
                    "severity": "critical",
                    "narrative": (
                        "High turnover risk coincides with low engagement "
                        "— this combination is the strongest predictor of "
                        "voluntary attrition."
                    ),
                }
            )

        # Low collaboration + low managers = silo risk
        if scores["collaboration"] < 45 and scores["managers"] < 50:
            insights.append(
                {
                    "type": "structural_risk",
                    "dimensions": ["collaboration", "managers"],
                    "severity": "high",
                    "narrative": (
                        "Weak collaboration combined with high manager dependency "
                        "suggests organizational silos forming around individual managers."
                    ),
                }
            )

        # Strong culture + weak performance = alignment gap
        if scores["culture"] > 70 and scores["performance"] < 40:
            insights.append(
                {
                    "type": "alignment_gap",
                    "dimensions": ["culture", "performance"],
                    "severity": "moderate",
                    "narrative": (
                        "Culture scores are healthy but performance lags "
                        "— teams may feel good but lack clarity on goals or "
                        "role expectations."
                    ),
                }
            )

        # High engagement + high collaboration = growth ready
        if scores["engagement"] > 70 and scores["collaboration"] > 65:
            insights.append(
                {
                    "type": "strength",
                    "dimensions": ["engagement", "collaboration"],
                    "severity": "positive",
                    "narrative": (
                        "Strong engagement and collaboration suggest the "
                        "organization is well-positioned for growth or "
                        "strategic change initiatives."
                    ),
                }
            )

        # Low culture + high turnover risk = culture-driven attrition
        if scores["culture"] < 40 and scores["turnover_risk"] < 45:
            insights.append(
                {
                    "type": "root_cause",
                    "dimensions": ["culture", "turnover_risk"],
                    "severity": "high",
                    "narrative": (
                        "Low culture health may be a root driver of elevated "
                        "turnover risk. Address psychological safety and "
                        "transparency before tactical retention efforts."
                    ),
                }
            )

        return insights

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _get_bi_team_health(self, db: AsyncSession, org_id: str) -> float:
        """Try to get average team health from Behavioral Intelligence."""
        try:
            from app.services.behavioral_intelligence_service import (
                BehavioralIntelligenceService,
            )

            bi = BehavioralIntelligenceService()
            dashboard = await bi.get_organization_dashboard(db, org_id)
            scores = dashboard.get("org_scores", {})
            if scores:
                vals = [
                    v for v in scores.values() if isinstance(v, (int, float)) and v > 0
                ]
                return sum(vals) / len(vals) if vals else 0
        except Exception:
            pass
        return 0

    async def _get_latest_snapshot(
        self, db: AsyncSession, org_id: str
    ) -> Optional[OrgDigitalTwinSnapshot]:
        query = (
            select(OrgDigitalTwinSnapshot)
            .where(
                and_(
                    OrgDigitalTwinSnapshot.organization_id == org_id,
                    OrgDigitalTwinSnapshot.is_simulation.is_(False),
                )
            )
            .order_by(desc(OrgDigitalTwinSnapshot.computed_at))
            .limit(1)
        )
        result = await db.execute(query)
        return result.scalar_one_or_none()

    def _is_fresh(self, snapshot: OrgDigitalTwinSnapshot) -> bool:
        """Consider a snapshot fresh if it's less than 1 hour old."""
        if not snapshot.computed_at:
            return False
        age = datetime.utcnow() - snapshot.computed_at.replace(tzinfo=None)
        return age < timedelta(hours=1)

    def _compute_trend(
        self, current_score: float, prev: Optional[OrgDigitalTwinSnapshot]
    ) -> str:
        if not prev:
            return "stable"
        delta = current_score - prev.overall_health_score
        if delta > 3:
            return "improving"
        elif delta < -3:
            return "declining"
        return "stable"

    def _snapshot_to_dict(self, s: OrgDigitalTwinSnapshot) -> Dict[str, Any]:
        return {
            "id": str(s.id),
            "organization_id": s.organization_id,
            "version": s.version,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
            "overall_health_score": s.overall_health_score,
            "overall_trend": s.overall_trend,
            "dimensions": {
                "teams": {"score": s.teams_score, **(s.state or {}).get("teams", {})},
                "managers": {
                    "score": s.managers_score,
                    **(s.state or {}).get("managers", {}),
                },
                "collaboration": {
                    "score": s.collaboration_score,
                    **(s.state or {}).get("collaboration", {}),
                },
                "performance": {
                    "score": s.performance_score,
                    **(s.state or {}).get("performance", {}),
                },
                "turnover_risk": {
                    "score": s.turnover_risk_score,
                    **(s.state or {}).get("turnover_risk", {}),
                },
                "engagement": {
                    "score": s.engagement_score,
                    **(s.state or {}).get("engagement", {}),
                },
                "culture": {
                    "score": s.culture_score,
                    **(s.state or {}).get("culture", {}),
                },
            },
            "data_sources": s.data_sources or {},
            "is_simulation": s.is_simulation,
        }

    def _snapshot_to_summary(self, s: OrgDigitalTwinSnapshot) -> Dict[str, Any]:
        return {
            "version": s.version,
            "computed_at": s.computed_at.isoformat() if s.computed_at else None,
            "overall_health_score": s.overall_health_score,
            "overall_trend": s.overall_trend,
            "scores": {
                "teams": s.teams_score,
                "managers": s.managers_score,
                "collaboration": s.collaboration_score,
                "performance": s.performance_score,
                "turnover_risk": s.turnover_risk_score,
                "engagement": s.engagement_score,
                "culture": s.culture_score,
            },
        }

    def _empty_dimension(self, reason: str) -> Dict[str, Any]:
        return {
            "score": 50,
            "highlights": [reason],
            "sub_metrics": {},
        }
