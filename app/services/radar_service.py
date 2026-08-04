"""
PsychSync Radar Service - Quick Win Dashboard
Aggregates toxicity detection, early warning, and behavioral analysis into unified 360° view
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.toxicity_detection import (
    BehavioralIntervention,
    PsychologicalSafetyMetrics,
    ToxicityLevel,
    ToxicityPattern,
)
from app.services.toxicity_detection_service import toxicity_detection_service

logger = logging.getLogger(__name__)


class RadarZone:
    """Radar zone classification"""

    GREEN = "green"  # Healthy - 0.0-0.3 risk
    YELLOW = "yellow"  # Emerging friction - 0.3-0.6 risk
    RED = "red"  # Toxic escalation - 0.6-1.0 risk


class RadarService:
    """
    Unified Radar Service - Aggregates multiple behavioral analysis services
    into a single 360° organizational health dashboard
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def get_radar_view(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """
        Get comprehensive radar view aggregating all behavioral signals

        Returns:
            - toxicity_analysis: Toxicity patterns and risks
            - early_warnings: Burnout and risk predictions
            - behavioral_patterns: Communication and behavioral metrics
            - psychological_safety: Team psychological safety scores
            - zone_classification: Green/yellow/red zone classification
            - intervention_status: Active interventions and their effectiveness
            - trends: Historical trend data
        """

        try:
            # Get toxicity analysis
            toxicity_data = await toxicity_detection_service.analyze_team_toxicity(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
                period_days=period_days,
            )

            # Get early warning data (burnout predictions)
            early_warnings = await self._get_early_warnings(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
            )

            # Get behavioral patterns
            behavioral_data = await self._get_behavioral_patterns(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
                period_days=period_days,
            )

            # Get psychological safety metrics
            psych_safety = await self._get_psychological_safety(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
            )

            # Get active interventions
            interventions = await self._get_active_interventions(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
            )

            # Calculate unified zone classification
            zone_classification = self._classify_zone(
                toxicity_data=toxicity_data,
                early_warnings=early_warnings,
                behavioral_data=behavioral_data,
                psych_safety=psych_safety,
            )

            # Get historical trends
            trends = await self._get_radar_trends(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
                days_back=90,
            )

            # Calculate concentric zone metrics
            concentric_zones = self._calculate_concentric_zones(
                toxicity_data=toxicity_data,
                behavioral_data=behavioral_data,
                psych_safety=psych_safety,
            )

            return {
                "organization_id": organization_id,
                "team_id": team_id,
                "analysis_date": datetime.utcnow().isoformat(),
                "period_days": period_days,
                # Core signal data
                "toxicity_analysis": toxicity_data,
                "early_warnings": early_warnings,
                "behavioral_patterns": behavioral_data,
                "psychological_safety": psych_safety,
                # Unified classification
                "zone_classification": zone_classification,
                "concentric_zones": concentric_zones,
                # Intervention tracking
                "active_interventions": interventions,
                # Trends
                "trends": trends,
                # Hotspot identification
                "hotspots": self._identify_hotspots(
                    toxicity_data=toxicity_data,
                    behavioral_data=behavioral_data,
                    zone_classification=zone_classification,
                ),
            }

        except Exception as e:
            self.logger.error(f"Failed to generate radar view: {e}", exc_info=True)
            return {
                "error": str(e),
                "zone_classification": {
                    "zone": RadarZone.GREEN,
                    "overall_risk_score": 0.0,
                    "confidence": 0.0,
                },
            }

    async def _get_early_warnings(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get early warning signals for burnout and risks"""

        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=14)

            # Query for high-risk patterns that could indicate burnout
            query = select(ToxicityPattern).filter(
                and_(
                    ToxicityPattern.organization_id == organization_id,
                    ToxicityPattern.detection_date >= cutoff_date,
                    ToxicityPattern.severity_level.in_(
                        [ToxicityLevel.HIGH, ToxicityLevel.CRITICAL]
                    ),
                )
            )

            if team_id:
                query = query.filter(ToxicityPattern.team_id == team_id)

            result = await db.execute(query)
            high_risk_patterns = result.scalars().all()

            # Calculate early warning metrics
            warning_count = len(high_risk_patterns)
            critical_count = len(
                [
                    p
                    for p in high_risk_patterns
                    if p.severity_level == ToxicityLevel.CRITICAL
                ]
            )

            # Calculate warning level
            if warning_count == 0:
                warning_level = "none"
                warning_score = 0.0
            elif warning_count <= 2:
                warning_level = "low"
                warning_score = 0.3
            elif warning_count <= 5:
                warning_level = "medium"
                warning_score = 0.6
            else:
                warning_level = "high"
                warning_score = 1.0

            return {
                "warning_level": warning_level,
                "warning_score": warning_score,
                "high_risk_patterns_count": warning_count,
                "critical_patterns_count": critical_count,
                "recent_patterns": [
                    {
                        "type": p.pattern_type,
                        "severity": p.severity_level,
                        "date": p.detection_date.isoformat(),
                    }
                    for p in sorted(
                        high_risk_patterns, key=lambda x: x.detection_date, reverse=True
                    )[:5]
                ],
                "prediction_horizon_days": 14,
            }

        except Exception as e:
            self.logger.error(f"Failed to get early warnings: {e}")
            return {
                "warning_level": "unknown",
                "warning_score": 0.0,
                "high_risk_patterns_count": 0,
                "critical_patterns_count": 0,
            }

    async def _get_behavioral_patterns(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
        period_days: int = 30,
    ) -> Dict[str, Any]:
        """Get behavioral pattern analysis"""

        try:
            cutoff_date = datetime.utcnow().date() - timedelta(days=period_days)

            # Get recent patterns for behavioral analysis
            query = select(ToxicityPattern).filter(
                and_(
                    ToxicityPattern.organization_id == organization_id,
                    ToxicityPattern.detection_date >= cutoff_date,
                )
            )

            if team_id:
                query = query.filter(ToxicityPattern.team_id == team_id)

            result = await db.execute(query)
            patterns = result.scalars().all()

            if not patterns:
                return {
                    "pattern_diversity": 0,
                    "most_common_patterns": [],
                    "behavioral_health_score": 1.0,
                    "trend_direction": "stable",
                }

            # Analyze pattern diversity
            pattern_types = [p.pattern_type for p in patterns]
            unique_types = len(set(pattern_types))
            pattern_diversity = unique_types / max(len(patterns), 1)

            # Most common patterns
            from collections import Counter

            pattern_counts = Counter(pattern_types)
            most_common = [
                {"type": ptype, "count": count}
                for ptype, count in pattern_counts.most_common(5)
            ]

            # Calculate behavioral health score (inverse of pattern frequency)
            behavioral_health = max(
                0.0, 1.0 - (len(patterns) / 50.0)
            )  # Normalize to 0-1

            # Determine trend
            recent_week = len(
                [
                    p
                    for p in patterns
                    if (datetime.utcnow().date() - p.detection_date).days <= 7
                ]
            )
            previous_week = len(
                [
                    p
                    for p in patterns
                    if 7 < (datetime.utcnow().date() - p.detection_date).days <= 14
                ]
            )

            if recent_week > previous_week * 1.2:
                trend = "increasing"  # More patterns = bad
            elif recent_week < previous_week * 0.8:
                trend = "decreasing"  # Fewer patterns = good
            else:
                trend = "stable"

            return {
                "pattern_diversity": round(pattern_diversity, 3),
                "most_common_patterns": most_common,
                "behavioral_health_score": round(behavioral_health, 3),
                "trend_direction": trend,
                "total_patterns": len(patterns),
                "pattern_frequency": round(len(patterns) / period_days, 2),
            }

        except Exception as e:
            self.logger.error(f"Failed to get behavioral patterns: {e}")
            return {
                "pattern_diversity": 0,
                "behavioral_health_score": 1.0,
                "trend_direction": "unknown",
            }

    async def _get_psychological_safety(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get psychological safety metrics"""

        try:
            query = (
                select(PsychologicalSafetyMetrics)
                .filter(PsychologicalSafetyMetrics.organization_id == organization_id)
                .order_by(PsychologicalSafetyMetrics.measurement_date.desc())
                .limit(1)
            )

            if team_id:
                query = query.filter(PsychologicalSafetyMetrics.team_id == team_id)

            result = await db.execute(query)
            latest_metrics = result.scalar_one_or_none()

            if not latest_metrics:
                return {
                    "overall_safety_score": None,
                    "risk_level": "unknown",
                    "components": {},
                }

            return {
                "overall_safety_score": float(latest_metrics.calculate_overall_score()),
                "risk_level": latest_metrics.get_risk_level(),
                "components": {
                    "speak_up_safety": (
                        float(latest_metrics.speak_up_safety)
                        if latest_metrics.speak_up_safety
                        else None
                    ),
                    "mistake_tolerance": (
                        float(latest_metrics.mistake_tolerance)
                        if latest_metrics.mistake_tolerance
                        else None
                    ),
                    "inclusion_safety": (
                        float(latest_metrics.inclusion_safety)
                        if latest_metrics.inclusion_safety
                        else None
                    ),
                    "learning_safety": (
                        float(latest_metrics.learning_safety)
                        if latest_metrics.learning_safety
                        else None
                    ),
                    "challenge_safety": (
                        float(latest_metrics.challenge_safety)
                        if latest_metrics.challenge_safety
                        else None
                    ),
                },
                "measurement_date": latest_metrics.measurement_date.isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Failed to get psychological safety: {e}")
            return {
                "overall_safety_score": None,
                "risk_level": "unknown",
            }

    async def _get_active_interventions(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get active intervention status"""

        try:
            # Get pattern IDs for this org
            pattern_query = select(ToxicityPattern.id).filter(
                ToxicityPattern.organization_id == organization_id
            )

            if team_id:
                pattern_query = pattern_query.filter(ToxicityPattern.team_id == team_id)

            pattern_result = await db.execute(pattern_query)
            pattern_ids = [row[0] for row in pattern_result.all()]

            if not pattern_ids:
                return {
                    "active_count": 0,
                    "by_priority": {},
                    "average_effectiveness": None,
                }

            # Get interventions
            intervention_query = select(BehavioralIntervention).filter(
                and_(
                    BehavioralIntervention.toxicity_pattern_id.in_(pattern_ids),
                    BehavioralIntervention.status.in_(["planned", "in_progress"]),
                )
            )

            result = await db.execute(intervention_query)
            interventions = result.scalars().all()

            # Count by priority
            priority_counts = {}
            total_effectiveness = 0.0
            effectiveness_count = 0

            for intervention in interventions:
                priority = intervention.priority_level
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

                if intervention.effectiveness_rating:
                    total_effectiveness += float(intervention.effectiveness_rating)
                    effectiveness_count += 1

            return {
                "active_count": len(interventions),
                "by_priority": priority_counts,
                "average_effectiveness": (
                    round(total_effectiveness / effectiveness_count, 2)
                    if effectiveness_count > 0
                    else None
                ),
                "recent_interventions": [
                    {
                        "id": str(i.id),
                        "type": i.intervention_type,
                        "priority": i.priority_level,
                        "status": i.status,
                        "created_at": i.created_at.isoformat(),
                    }
                    for i in sorted(
                        interventions, key=lambda x: x.created_at, reverse=True
                    )[:5]
                ],
            }

        except Exception as e:
            self.logger.error(f"Failed to get active interventions: {e}")
            return {
                "active_count": 0,
                "by_priority": {},
            }

    def _classify_zone(
        self,
        toxicity_data: Dict[str, Any],
        early_warnings: Dict[str, Any],
        behavioral_data: Dict[str, Any],
        psych_safety: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Classify organization/team into green/yellow/red zone based on all signals

        Zone classification logic:
        - GREEN (0.0-0.3): Healthy, low toxicity, good psych safety
        - YELLOW (0.3-0.6): Emerging issues, moderate risk
        - RED (0.6-1.0): Critical issues, immediate intervention needed
        """

        risk_components = []

        # Toxicity risk (0.0-1.0)
        toxicity_risk = toxicity_data.get("risk_score", 0.0)
        risk_components.append(("toxicity", toxicity_risk, 0.35))

        # Early warning risk (0.0-1.0)
        warning_risk = early_warnings.get("warning_score", 0.0)
        risk_components.append(("early_warning", warning_risk, 0.25))

        # Behavioral health (inverted - lower health = higher risk)
        behavioral_health = behavioral_data.get("behavioral_health_score", 1.0)
        behavioral_risk = 1.0 - behavioral_health
        risk_components.append(("behavioral", behavioral_risk, 0.20))

        # Psychological safety (inverted - lower safety = higher risk)
        psych_safety_score = psych_safety.get("overall_safety_score", 0.8)
        if psych_safety_score is not None:
            psych_risk = 1.0 - psych_safety_score
        else:
            psych_risk = 0.0
        risk_components.append(("psychological_safety", psych_risk, 0.20))

        # Calculate weighted risk score
        total_weight = sum(weight for _, _, weight in risk_components)
        weighted_risk = (
            sum(risk * weight for _, risk, weight in risk_components) / total_weight
        )

        # Classify zone
        if weighted_risk >= 0.6:
            zone = RadarZone.RED
            zone_label = "Critical"
        elif weighted_risk >= 0.3:
            zone = RadarZone.YELLOW
            zone_label = "Caution"
        else:
            zone = RadarZone.GREEN
            zone_label = "Healthy"

        return {
            "zone": zone,
            "zone_label": zone_label,
            "overall_risk_score": round(weighted_risk, 3),
            "confidence": round(
                min(1.0, weighted_risk * 1.5), 3
            ),  # Higher risk = higher confidence
            "risk_components": [
                {"component": name, "risk": round(risk, 3), "weight": weight}
                for name, risk, weight in risk_components
            ],
            "recommendation": self._get_zone_recommendation(zone, weighted_risk),
        }

    def _calculate_concentric_zones(
        self,
        toxicity_data: Dict[str, Any],
        behavioral_data: Dict[str, Any],
        psych_safety: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate concentric zone metrics for radar visualization

        Inner zone: Individual behaviors (toxicity patterns)
        Middle zone: Team dynamics (behavioral patterns)
        Outer zone: Organizational health (psychological safety)
        """

        # Inner zone - Individual toxicity
        inner_zone_risk = toxicity_data.get("risk_score", 0.0)
        inner_zone_size = len(toxicity_data.get("patterns_detected", []))

        # Middle zone - Team behavioral patterns
        middle_zone_health = behavioral_data.get("behavioral_health_score", 1.0)
        middle_zone_risk = 1.0 - middle_zone_health

        # Outer zone - Organizational psychological safety
        outer_zone_safety = psych_safety.get("overall_safety_score", 0.8)
        if outer_zone_safety is not None:
            outer_zone_risk = 1.0 - outer_zone_safety
        else:
            outer_zone_risk = 0.2  # Default low risk if no data

        return {
            "inner_zone": {
                "name": "Individual Behaviors",
                "risk_score": round(inner_zone_risk, 3),
                "indicator_count": inner_zone_size,
                "zone": self._risk_to_zone(inner_zone_risk),
            },
            "middle_zone": {
                "name": "Team Dynamics",
                "risk_score": round(middle_zone_risk, 3),
                "health_score": round(middle_zone_health, 3),
                "zone": self._risk_to_zone(middle_zone_risk),
            },
            "outer_zone": {
                "name": "Organizational Health",
                "risk_score": round(outer_zone_risk, 3),
                "safety_score": outer_zone_safety,
                "zone": self._risk_to_zone(outer_zone_risk),
            },
        }

    def _risk_to_zone(self, risk_score: float) -> str:
        """Convert risk score to zone classification"""
        if risk_score >= 0.6:
            return RadarZone.RED
        elif risk_score >= 0.3:
            return RadarZone.YELLOW
        else:
            return RadarZone.GREEN

    def _get_zone_recommendation(self, zone: str, risk_score: float) -> str:
        """Get actionable recommendation based on zone"""

        if zone == RadarZone.RED:
            return (
                f"CRITICAL: Risk score of {risk_score:.1%} indicates serious issues. "
                "Immediate intervention required. Review toxic patterns, activate HR protocols, "
                "and address high-risk behaviors within 24-48 hours."
            )
        elif zone == RadarZone.YELLOW:
            return (
                f"CAUTION: Risk score of {risk_score:.1%} indicates emerging concerns. "
                "Monitor closely, implement preventive measures, and check in with affected teams "
                "within the next week."
            )
        else:
            return (
                f"HEALTHY: Risk score of {risk_score:.1%} indicates positive environment. "
                "Continue monitoring, maintain current practices, and share best practices "
                "to sustain healthy culture."
            )

    def _identify_hotspots(
        self,
        toxicity_data: Dict[str, Any],
        behavioral_data: Dict[str, Any],
        zone_classification: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify specific hotspots requiring attention"""

        hotspots = []

        # Toxicity hotspots
        patterns = toxicity_data.get("patterns_detected", [])
        for pattern in patterns[:3]:  # Top 3
            if pattern.get("severity_score", 0) > 0.5:
                hotspots.append(
                    {
                        "type": "toxicity",
                        "severity": pattern.get("severity_score", 0),
                        "description": f"{pattern.get('type', 'Unknown')} pattern detected",
                        "priority": (
                            "high"
                            if pattern.get("severity_score", 0) > 0.7
                            else "medium"
                        ),
                    }
                )

        # Behavioral hotspots
        common_patterns = behavioral_data.get("most_common_patterns", [])
        for pattern in common_patterns[:2]:  # Top 2
            if pattern.get("count", 0) > 2:
                hotspots.append(
                    {
                        "type": "behavioral",
                        "severity": min(1.0, pattern.get("count", 0) / 10.0),
                        "description": f"Recurring {pattern.get('type', 'Unknown')} behavior",
                        "priority": "medium",
                    }
                )

        # Sort by severity
        hotspots.sort(key=lambda x: x.get("severity", 0), reverse=True)

        return hotspots[:5]  # Return top 5

    async def _get_radar_trends(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
        days_back: int = 90,
    ) -> Dict[str, Any]:
        """Get historical trend data for radar visualization"""

        try:
            trends = toxicity_detection_service.get_toxicity_trends(
                db=db,
                organization_id=organization_id,
                team_id=team_id,
                days_back=days_back,
            )

            return trends

        except Exception as e:
            self.logger.error(f"Failed to get radar trends: {e}")
            return {
                "trend_data": [],
                "summary": {
                    "trend_direction": "unknown",
                },
            }


# Singleton instance
radar_service = RadarService()
