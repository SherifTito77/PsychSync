"""
Corporate Psychology Encoding Service
System-level organizational psychology analysis for executive decision-making

This service implements the 6 core psychology encodings:
1. Cognitive Load Index (CLI)
2. Trust Stability Curve (TSC)
3. Emotional Volatility Signal (EVS)
4. Coordination Friction Score (CFS)
5. Psychological Debt Accumulation (PDA)
6. Recovery & Resilience Capacity (RRC)

All analysis is at ORGANIZATIONAL/SYSTEM level - NO individual diagnostics.
"""

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

from sqlalchemy import and_
from sqlalchemy import func as sql_func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from app.db.models.corporate_psychology import (
    CorporatePsychologyMetrics,
    InterventionCategory,
    InterventionStatus,
    RiskHorizon,
    StructuralIntervention,
    SystemSignalAlert,
)

logger = logging.getLogger(__name__)


@dataclass
class EncodingCalculation:
    """Result of a psychology encoding calculation."""

    value: float
    trend: str  # 'improving', 'stable', 'declining'
    slope: float  # Rate of change
    acceleration: Optional[float] = None  # Change in slope
    confidence: float = 0.0  # 0-100
    drivers: Optional[dict[str, Any]] = None


@dataclass
class SystemSignal:
    """Early-warning signal for organizational issues."""

    alert_type: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    risk_horizon: str  # 'immediate', 'emerging', 'structural'
    summary: str
    description: str
    rate_of_change: float
    operational_impact: str
    affected_encodings: list[str]
    current_value: float
    baseline_value: Optional[float]
    probability_range: str
    recommended_actions: list[str]
    urgency: str


@dataclass
class InterventionRecommendation:
    """Recommended structural intervention."""

    title: str
    description: str
    category: InterventionCategory
    target_encodings: list[str]
    expected_outcomes: str
    business_rationale: str
    implementation_approach: str
    estimated_duration_weeks: int
    resource_requirements: str


class CorporatePsychologyService:
    """
    Service for encoding organizational psychology into actionable intelligence

    Operates at system level, NOT individual level.
    All metrics are aggregated at team/organization level.
    """

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.logger = logging.getLogger("corporate_psychology")

    # ═══════════════════════════════════════════════════════════════
    # CORE ENCODING CALCULATIONS
    # ═══════════════════════════════════════════════════════════════

    def calculate_cognitive_load_index(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Cognitive Load Index (CLI)

        CLI measures overall cognitive burden on the organization based on:
        - Communication volume and complexity
        - Meeting density and duration
        - Task switching frequency
        - Information processing demands
        - Decision-making pressure

        Returns: EncodingCalculation with CLI score (0-100, higher = more cognitive strain)
        """
        try:
            self.logger.info(f"Calculating CLI for org {organization_id}")

            # Extract data from sources
            communication_metrics = data_sources.get("communication_metrics", {})
            meeting_metrics = data_sources.get("meeting_metrics", {})
            workload_metrics = data_sources.get("workload_metrics", {})

            # Core CLI components
            communication_load = self._calculate_communication_load(
                communication_metrics
            )
            meeting_cognitive_cost = self._calculate_meeting_cognitive_cost(
                meeting_metrics
            )
            task_switching_cost = self._calculate_task_switching_cost(workload_metrics)
            decision_complexity = self._calculate_decision_complexity(
                communication_metrics
            )
            information_overload = self._calculate_information_overload(
                communication_metrics
            )

            # Weighted composite (weights can be adjusted per organization)
            cli = (
                communication_load * 0.25
                + meeting_cognitive_cost * 0.20
                + task_switching_cost * 0.20
                + decision_complexity * 0.20
                + information_overload * 0.15
            )

            # Calculate trend by comparing to baseline
            baseline = data_sources.get("baseline_cli", 50.0)
            slope = cli - baseline
            trend = self._determine_trend(slope, threshold=5.0)

            # Calculate acceleration if historical data available
            acceleration = self._calculate_acceleration(
                data_sources.get("historical_cli_values", []), cli
            )

            # Identify key drivers
            drivers = {
                "communication_load": communication_load,
                "meeting_cognitive_cost": meeting_cognitive_cost,
                "task_switching_cost": task_switching_cost,
                "decision_complexity": decision_complexity,
                "information_overload": information_overload,
                "primary_driver": max(
                    [
                        ("communication", communication_load),
                        ("meetings", meeting_cognitive_cost),
                        ("task_switching", task_switching_cost),
                        ("decision_complexity", decision_complexity),
                        ("info_overload", information_overload),
                    ],
                    key=lambda x: x[1],
                )[0],
            }

            # Confidence based on data quality
            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(cli, 2),
                trend=trend,
                slope=round(slope, 2),
                acceleration=round(acceleration, 3) if acceleration else None,
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate CLI: {e}")
            # Return default calculation on error
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    def calculate_trust_stability_curve(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Trust Stability Curve (TSC)

        TSC measures stability and strength of trust across the organization based on:
        - Cross-team collaboration quality
        - Leadership trust indicators
        - Transparency and information sharing
        - Psychological safety metrics
        - Communication pattern consistency

        Returns: EncodingCalculation with TSC score (0-100, higher = more stable trust)
        """
        try:
            self.logger.info(f"Calculating TSC for org {organization_id}")

            culture_metrics = data_sources.get("culture_metrics", {})
            behavioral_metrics = data_sources.get("behavioral_metrics", {})

            # Core TSC components
            psychological_safety = culture_metrics.get("psychological_safety_score", 50)
            transparency_score = culture_metrics.get("transparency_score", 50)
            collaboration_effectiveness = culture_metrics.get(
                "collaboration_effectiveness", 50
            )
            trust_indicators = culture_metrics.get("trust_indicators", {})
            cross_team_collaboration = behavioral_metrics.get("cross_team_score", 50)

            # Extract trust indicators if available
            honesty_score = (
                trust_indicators.get("honesty", 50)
                if isinstance(trust_indicators, dict)
                else 50
            )
            information_sharing = (
                trust_indicators.get("information_sharing", 50)
                if isinstance(trust_indicators, dict)
                else 50
            )

            # Weighted composite
            tsc = (
                psychological_safety * 0.25
                + transparency_score * 0.20
                + collaboration_effectiveness * 0.20
                + cross_team_collaboration * 0.20
                + honesty_score * 0.15
            )

            # Calculate volatility (standard deviation from ideal)
            volatility = self._calculate_trust_volatility(culture_metrics)

            # Determine trend
            baseline = data_sources.get("baseline_tsc", 50.0)
            slope = tsc - baseline
            trend = (
                "strengthening"
                if slope > 5.0
                else "eroding" if slope < -5.0 else "stable"
            )

            drivers = {
                "psychological_safety": psychological_safety,
                "transparency": transparency_score,
                "collaboration": collaboration_effectiveness,
                "cross_team_trust": cross_team_collaboration,
                "volatility": volatility,
                "primary_factor": (
                    "high_volatility" if volatility > 20 else "stable_patterns"
                ),
            }

            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(tsc, 2),
                trend=trend,
                slope=round(slope, 2),
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate TSC: {e}")
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    def calculate_emotional_volatility_signal(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Emotional Volatility Signal (EVS)

        EVS measures emotional regulation and stability at organizational level based on:
        - Sentiment variance in communications
        - Stress level indicators
        - Conflict and tension patterns
        - Recovery time from stress events
        - Emotional contagion patterns

        Returns: EncodingCalculation with EVS score (0-100, higher = more volatility)
        """
        try:
            self.logger.info(f"Calculating EVS for org {organization_id}")

            wellness_metrics = data_sources.get("wellness_metrics", {})
            communication_metrics = data_sources.get("communication_metrics", {})
            culture_metrics = data_sources.get("culture_metrics", {})

            # Core EVS components
            stress_level = wellness_metrics.get("average_stress_level", 50)
            sentiment_variance = communication_metrics.get("sentiment_variance", 30)
            conflict_level = culture_metrics.get("conflict_level", 30)
            exhaustion_level = wellness_metrics.get("average_exhaustion", 40)
            emotional_instability = communication_metrics.get(
                "emotional_volatility", 30
            )

            # Normalize conflict level if it's a string
            if isinstance(conflict_level, str):
                conflict_map = {"low": 20, "medium": 50, "high": 80, "critical": 95}
                conflict_level = conflict_map.get(conflict_level.lower(), 50)

            # Weighted composite (higher = more volatile)
            evs = (
                stress_level * 0.25
                + sentiment_variance * 0.25
                + conflict_level * 0.20
                + exhaustion_level * 0.15
                + emotional_instability * 0.15
            )

            # Identify triggers
            triggers = self._identify_volatility_triggers(data_sources)

            # Calculate recovery time
            recovery_time = self._calculate_recovery_time(wellness_metrics)

            baseline = data_sources.get("baseline_evs", 50.0)
            slope = evs - baseline
            trend = (
                "increasing"
                if slope > 5.0
                else "decreasing" if slope < -5.0 else "stable"
            )

            drivers = {
                "stress_contribution": stress_level,
                "sentiment_variance": sentiment_variance,
                "conflict_contribution": conflict_level,
                "exhaustion_contribution": exhaustion_level,
                "identified_triggers": triggers,
                "recovery_time": recovery_time,
            }

            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(evs, 2),
                trend=trend,
                slope=round(slope, 2),
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate EVS: {e}")
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    def calculate_coordination_friction_score(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Coordination Friction Score (CFS)

        CFS measures efficiency and smoothness of organizational coordination based on:
        - Handoff efficiency between teams
        - Bottleneck identification
        - Dependency loop detection
        - Communication delay patterns
        - Decision latency

        Returns: EncodingCalculation with CFS score (0-100, higher = more friction)
        """
        try:
            self.logger.info(f"Calculating CFS for org {organization_id}")

            behavioral_metrics = data_sources.get("behavioral_metrics", {})
            communication_metrics = data_sources.get("communication_metrics", {})
            team_metrics = data_sources.get("team_metrics", {})

            # Core CFS components
            handoff_efficiency = behavioral_metrics.get("handoff_efficiency", 50)
            bottleneck_severity = behavioral_metrics.get("bottleneck_score", 50)
            dependency_complexity = behavioral_metrics.get("dependency_complexity", 50)
            communication_delay = communication_metrics.get("response_delay_score", 40)
            decision_latency = behavioral_metrics.get("decision_latency", 40)

            # Count dependency loops
            dependency_loops = behavioral_metrics.get("dependency_loop_count", 0)

            # Weighted composite (higher = more friction)
            # Note: handoff_efficiency is inverted (100 - efficiency)
            cfs = (
                (100 - handoff_efficiency) * 0.25
                + bottleneck_severity * 0.25
                + dependency_complexity * 0.20
                + communication_delay * 0.15
                + decision_latency * 0.15
            )

            # Cap at 100
            cfs = min(cfs, 100)

            baseline = data_sources.get("baseline_cfs", 50.0)
            slope = cfs - baseline
            trend = (
                "increasing"
                if slope > 5.0
                else "decreasing" if slope < -5.0 else "stable"
            )

            drivers = {
                "handoff_friction": 100 - handoff_efficiency,
                "bottleneck_score": bottleneck_severity,
                "dependency_loops": dependency_loops,
                "communication_delay": communication_delay,
                "decision_latency": decision_latency,
                "primary_bottleneck": behavioral_metrics.get(
                    "primary_bottleneck", "unknown"
                ),
            }

            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(cfs, 2),
                trend=trend,
                slope=round(slope, 2),
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate CFS: {e}")
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    def calculate_psychological_debt_accumulation(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Psychological Debt Accumulation (PDA)

        PDA measures accumulated strain and unresolved psychological issues based on:
        - Chronic workload patterns
        - Unresolved conflicts
        - Accumulated stress
        - Recovery deficit
        - Wellness trend deterioration

        Returns: EncodingCalculation with PDA score (0-100, higher = more debt)
        """
        try:
            self.logger.info(f"Calculating PDA for org {organization_id}")

            wellness_metrics = data_sources.get("wellness_metrics", {})
            culture_metrics = data_sources.get("culture_metrics", {})

            # Core PDA components
            chronic_workload = wellness_metrics.get("chronic_workload_score", 40)
            unresolved_conflicts = culture_metrics.get("unresolved_conflict_score", 30)
            accumulated_stress = wellness_metrics.get("accumulated_stress", 50)
            recovery_deficit = wellness_metrics.get("recovery_deficit", 40)
            wellness_deterioration = wellness_metrics.get(
                "wellness_deterioration_rate", 30
            )

            # Calculate debt rate (debt accumulation per time period)
            debt_rate = self._calculate_debt_rate(wellness_metrics)

            # Calculate paydown capacity
            paydown_capacity = self._calculate_paydown_capacity(wellness_metrics)

            # Weighted composite (higher = more debt)
            pda = (
                chronic_workload * 0.25
                + unresolved_conflicts * 0.20
                + accumulated_stress * 0.25
                + recovery_deficit * 0.15
                + wellness_deterioration * 0.15
            )

            # Break down debt by category
            debt_categories = {
                "workload_debt": chronic_workload,
                "conflict_debt": unresolved_conflicts,
                "stress_debt": accumulated_stress,
                "recovery_debt": recovery_deficit,
            }

            baseline = data_sources.get("baseline_pda", 50.0)
            slope = pda - baseline
            trend = (
                "accumulating"
                if slope > 5.0
                else "paying_down" if slope < -5.0 else "stable"
            )

            drivers = {
                "debt_categories": debt_categories,
                "debt_rate": debt_rate,
                "paydown_capacity": paydown_capacity,
                "debt_ratio": pda / max(paydown_capacity, 1),  # Debt to capacity ratio
            }

            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(pda, 2),
                trend=trend,
                slope=round(slope, 2),
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate PDA: {e}")
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    def calculate_recovery_resilience_capacity(
        self,
        organization_id: str,
        measurement_period_start: date,
        measurement_period_end: date,
        data_sources: dict[str, Any],
    ) -> EncodingCalculation:
        """
        Calculate Recovery & Resilience Capacity (RRC)

        RRC measures organization's ability to recover and bounce back based on:
        - Historical recovery patterns
        - Adaptation speed to stressors
        - Learning from setbacks
        - Support system quality
        - Resource availability

        Returns: EncodingCalculation with RRC score (0-100, higher = more resilient)
        """
        try:
            self.logger.info(f"Calculating RRC for org {organization_id}")

            wellness_metrics = data_sources.get("wellness_metrics", {})
            team_metrics = data_sources.get("team_metrics", {})
            culture_metrics = data_sources.get("culture_metrics", {})

            # Core RRC components
            historical_recovery = wellness_metrics.get("recovery_rate", 50)
            adaptation_speed = team_metrics.get("adaptation_score", 50)
            learning_rate = culture_metrics.get("learning_orientation", 50)
            support_quality = wellness_metrics.get("support_quality", 50)
            resource_availability = team_metrics.get("resource_availability", 50)

            # Calculate resilience buffer (margin before crisis)
            resilience_buffer = self._calculate_resilience_buffer(wellness_metrics)

            # Weighted composite (higher = more resilient)
            rrc = (
                historical_recovery * 0.25
                + adaptation_speed * 0.25
                + learning_rate * 0.20
                + support_quality * 0.15
                + resource_availability * 0.15
            )

            baseline = data_sources.get("baseline_rrc", 50.0)
            slope = rrc - baseline
            trend = (
                "strengthening"
                if slope > 5.0
                else "weakening" if slope < -5.0 else "stable"
            )

            drivers = {
                "resilience_buffer": resilience_buffer,
                "adaptation_speed": adaptation_speed,
                "learning_capacity": learning_rate,
                "support_quality": support_quality,
                "crisis_threshold": resilience_buffer
                * 0.7,  # Threshold for crisis mode
            }

            confidence = self._calculate_confidence(data_sources)

            return EncodingCalculation(
                value=round(rrc, 2),
                trend=trend,
                slope=round(slope, 2),
                confidence=confidence,
                drivers=drivers,
            )

        except Exception as e:
            self.logger.error(f"Failed to calculate RRC: {e}")
            return EncodingCalculation(
                value=50.0, trend="stable", slope=0.0, confidence=0.0
            )

    # ═══════════════════════════════════════════════════════════════
    # AGGREGATE METRICS
    # ═══════════════════════════════════════════════════════════════

    def calculate_organizational_health_index(
        self,
        cli: EncodingCalculation,
        tsc: EncodingCalculation,
        evs: EncodingCalculation,
        cfs: EncodingCalculation,
        pda: EncodingCalculation,
        rrc: EncodingCalculation,
    ) -> float:
        """
        Calculate overall Organizational Health Index

        Composite of all 6 psychology encodings.
        Higher = healthier organization (0-100 scale)
        """
        # Invert "bad" metrics (lower is better)
        cli_normalized = 100 - cli.value  # Cognitive load: lower is better
        evs_normalized = 100 - evs.value  # Volatility: lower is better
        cfs_normalized = 100 - cfs.value  # Friction: lower is better
        pda_normalized = 100 - pda.value  # Debt: lower is better

        # Keep "good" metrics as-is
        tsc_normalized = tsc.value  # Trust: higher is better
        rrc_normalized = rrc.value  # Resilience: higher is better

        # Weighted composite
        health_index = (
            cli_normalized * 0.18
            + tsc_normalized * 0.18
            + evs_normalized * 0.16
            + cfs_normalized * 0.16
            + pda_normalized * 0.16
            + rrc_normalized * 0.16
        )

        return round(health_index, 2)

    def calculate_overall_risk_score(
        self,
        health_index: float,
        encodings: dict[str, EncodingCalculation],
    ) -> float:
        """
        Calculate overall risk score for the organization

        Higher = more risk (0-100 scale)
        """
        # Risk is inverse of health
        base_risk = 100 - health_index

        # Adjust for critical risk factors
        risk_multipliers = []

        # High cognitive load increases risk
        if encodings["cli"].value > 75:
            risk_multipliers.append(1.2)

        # Low trust increases risk
        if encodings["tsc"].value < 40:
            risk_multipliers.append(1.3)

        # High volatility increases risk
        if encodings["evs"].value > 70:
            risk_multipliers.append(1.25)

        # High friction increases risk
        if encodings["cfs"].value > 70:
            risk_multipliers.append(1.15)

        # High debt increases risk
        if encodings["pda"].value > 75:
            risk_multipliers.append(1.3)

        # Low resilience increases risk
        if encodings["rrc"].value < 40:
            risk_multipliers.append(1.2)

        # Apply multipliers
        final_risk = base_risk
        for multiplier in risk_multipliers:
            final_risk *= multiplier

        return round(min(final_risk, 100), 2)

    # ═══════════════════════════════════════════════════════════════
    # ALERT GENERATION
    # ═══════════════════════════════════════════════════════════════

    def generate_system_signals(
        self,
        organization_id: str,
        encodings: dict[str, EncodingCalculation],
        health_index: float,
        risk_score: float,
    ) -> list[SystemSignal]:
        """
        Generate early-warning signals based on psychology encodings

        Returns list of SystemSignal alerts for thresholds that have been crossed
        """
        signals = []

        # Check CLI (Cognitive Load Index)
        if encodings["cli"].value > 75:
            signals.append(
                SystemSignal(
                    alert_type="cognitive_overload",
                    severity="critical" if encodings["cli"].value > 85 else "high",
                    risk_horizon=(
                        "immediate" if encodings["cli"].slope > 10 else "emerging"
                    ),
                    summary="Organizational cognitive load exceeding sustainable thresholds",
                    description=self._format_cli_alert(encodings["cli"]),
                    rate_of_change=encodings["cli"].slope,
                    operational_impact="This pattern increases execution risk and decision errors within 14-30 days",
                    affected_encodings=["CLI", "EVS", "CFS"],
                    current_value=encodings["cli"].value,
                    baseline_value=encodings["cli"].value - encodings["cli"].slope,
                    probability_range=(
                        "70-85%" if encodings["cli"].value > 80 else "55-70%"
                    ),
                    recommended_actions=[
                        "Implement communication throttle (reduce meeting density by 20-30%)",
                        "Establish decision-making protocols to reduce decision fatigue",
                        "Create focus blocks for deep work with minimal interruptions",
                    ],
                    urgency="critical" if encodings["cli"].value > 85 else "high",
                )
            )

        # Check TSC (Trust Stability)
        if encodings["tsc"].value < 45:
            signals.append(
                SystemSignal(
                    alert_type="trust_erosion",
                    severity="critical" if encodings["tsc"].value < 35 else "high",
                    risk_horizon="structural",
                    summary="Trust stability showing erosion patterns",
                    description=self._format_tsc_alert(encodings["tsc"]),
                    rate_of_change=encodings["tsc"].slope,
                    operational_impact="Trust erosion increases collaboration friction and reduces innovation velocity over 45+ days",
                    affected_encodings=["TSC", "CFS", "RRC"],
                    current_value=encodings["tsc"].value,
                    baseline_value=encodings["tsc"].value - encodings["tsc"].slope,
                    probability_range=(
                        "60-75%" if encodings["tsc"].value < 40 else "45-60%"
                    ),
                    recommended_actions=[
                        "Increase transparency in decision-making processes",
                        "Establish regular town hall meetings for leadership communication",
                        "Create cross-team collaboration initiatives to rebuild trust",
                    ],
                    urgency="high",
                )
            )

        # Check EVS (Emotional Volatility)
        if encodings["evs"].value > 70:
            signals.append(
                SystemSignal(
                    alert_type="emotional_volatility",
                    severity="critical" if encodings["evs"].value > 80 else "high",
                    risk_horizon=(
                        "immediate" if encodings["evs"].slope > 10 else "emerging"
                    ),
                    summary="Elevated emotional volatility detected",
                    description=self._format_evs_alert(encodings["evs"]),
                    rate_of_change=encodings["evs"].slope,
                    operational_impact="High volatility increases conflict risk and reduces collaboration effectiveness within 14-21 days",
                    affected_encodings=["EVS", "CLI", "TSC"],
                    current_value=encodings["evs"].value,
                    baseline_value=encodings["evs"].value - encodings["evs"].slope,
                    probability_range=(
                        "75-90%" if encodings["evs"].value > 80 else "60-75%"
                    ),
                    recommended_actions=[
                        "Identify and address volatility triggers using root cause analysis",
                        "Implement stress-reduction protocols and resources",
                        "Facilitate mediated discussions for conflict resolution",
                    ],
                    urgency="critical" if encodings["evs"].value > 80 else "high",
                )
            )

        # Check CFS (Coordination Friction)
        if encodings["cfs"].value > 70:
            signals.append(
                SystemSignal(
                    alert_type="coordination_friction",
                    severity="high" if encodings["cfs"].value > 80 else "medium",
                    risk_horizon="emerging",
                    summary="Significant coordination friction detected",
                    description=self._format_cfs_alert(encodings["cfs"]),
                    rate_of_change=encodings["cfs"].slope,
                    operational_impact="Coordination friction reduces delivery velocity and increases error rates within 30-45 days",
                    affected_encodings=["CFS", "CLI", "PDA"],
                    current_value=encodings["cfs"].value,
                    baseline_value=encodings["cfs"].value - encodings["cfs"].slope,
                    probability_range=(
                        "65-80%" if encodings["cfs"].value > 75 else "50-65%"
                    ),
                    recommended_actions=[
                        "Map and address bottlenecks in handoff processes",
                        "Reduce dependency loops through architectural improvements",
                        "Implement clearer ownership and decision matrices",
                    ],
                    urgency="high" if encodings["cfs"].value > 80 else "medium",
                )
            )

        # Check PDA (Psychological Debt)
        if encodings["pda"].value > 75:
            signals.append(
                SystemSignal(
                    alert_type="psychological_debt_critical",
                    severity="critical" if encodings["pda"].value > 85 else "high",
                    risk_horizon="structural",
                    summary="Psychological debt approaching critical levels",
                    description=self._format_pda_alert(encodings["pda"]),
                    rate_of_change=encodings["pda"].slope,
                    operational_impact="Critical debt levels increase burnout risk and reduce capacity within 45-60 days",
                    affected_encodings=["PDA", "RRC", "CLI"],
                    current_value=encodings["pda"].value,
                    baseline_value=encodings["pda"].value - encodings["pda"].slope,
                    probability_range=(
                        "80-90%" if encodings["pda"].value > 85 else "65-80%"
                    ),
                    recommended_actions=[
                        "Implement debt paydown initiative with reduced workload",
                        "Hiring or resource allocation to address capacity gap",
                        "Sprint/quarter focused on technical debt and process improvement",
                    ],
                    urgency="critical" if encodings["pda"].value > 85 else "high",
                )
            )

        # Check RRC (Recovery & Resilience)
        if encodings["rrc"].value < 40:
            signals.append(
                SystemSignal(
                    alert_type="resilience_deficit",
                    severity="critical" if encodings["rrc"].value < 30 else "high",
                    risk_horizon="structural",
                    summary="Insufficient recovery and resilience capacity",
                    description=self._format_rrc_alert(encodings["rrc"]),
                    rate_of_change=encodings["rrc"].slope,
                    operational_impact="Low resilience increases vulnerability to stressors and reduces adaptability over 60+ days",
                    affected_encodings=["RRC", "PDA", "EVS"],
                    current_value=encodings["rrc"].value,
                    baseline_value=encodings["rrc"].value - encodings["rrc"].slope,
                    probability_range=(
                        "70-85%" if encodings["rrc"].value < 35 else "55-70%"
                    ),
                    recommended_actions=[
                        "Invest in support systems and resources",
                        "Implement adaptation and learning programs",
                        "Create buffer capacity in teams and processes",
                    ],
                    urgency="critical" if encodings["rrc"].value < 30 else "high",
                )
            )

        return signals

    # ═══════════════════════════════════════════════════════════════
    # INTERVENTION RECOMMENDATIONS
    # ═══════════════════════════════════════════════════════════════

    def generate_intervention_recommendations(
        self,
        signals: list[SystemSignal],
        encodings: dict[str, EncodingCalculation],
    ) -> list[InterventionRecommendation]:
        """
        Generate structural intervention recommendations based on signals

        Returns list of recommended interventions with business rationale
        """
        recommendations = []

        for signal in signals:
            if signal.alert_type == "cognitive_overload":
                recommendations.append(
                    InterventionRecommendation(
                        title="Communication Cadence Optimization",
                        description="Restructure meeting and communication patterns to reduce cognitive load",
                        category=InterventionCategory.CADENCE,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="20-30% reduction in cognitive load, improved decision quality",
                        business_rationale="Reduced cognitive load directly improves execution velocity and reduces error rates in decision-making",
                        implementation_approach="Implement meeting-free zones, async-first communication policy, and decision delegation framework",
                        estimated_duration_weeks=4,
                        resource_requirements="Leadership alignment, communication guidelines, minimal budget",
                    )
                )

            elif signal.alert_type == "trust_erosion":
                recommendations.append(
                    InterventionRecommendation(
                        title="Transparency & Communication Enhancement",
                        description="Increase organizational transparency and improve communication patterns",
                        category=InterventionCategory.COMMUNICATION,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="15-25% improvement in trust stability, reduced collaboration friction",
                        business_rationale="Trust is the foundation of effective collaboration - improving trust directly increases innovation velocity",
                        implementation_approach="Regular town halls, decision transparency documents, open Q&A sessions",
                        estimated_duration_weeks=8,
                        resource_requirements="Leadership time commitment, communication platform, facilitation resources",
                    )
                )

            elif signal.alert_type == "emotional_volatility":
                recommendations.append(
                    InterventionRecommendation(
                        title="Stress Reduction & Emotional Support Protocol",
                        description="Implement organizational stress reduction and emotional support mechanisms",
                        category=InterventionCategory.PROCESS,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="25-35% reduction in emotional volatility, improved team stability",
                        business_rationale="Reduced volatility decreases conflict overhead and increases collaboration efficiency",
                        implementation_approach="Volatility trigger identification, stress management resources, conflict resolution training",
                        estimated_duration_weeks=6,
                        resource_requirements="HR support, training budget, wellness resources",
                    )
                )

            elif signal.alert_type == "coordination_friction":
                recommendations.append(
                    InterventionRecommendation(
                        title="Process Optimization & Bottleneck Removal",
                        description="Identify and eliminate coordination bottlenecks",
                        category=InterventionCategory.PROCESS,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="30-40% reduction in coordination friction, improved delivery velocity",
                        business_rationale="Process efficiency directly impacts delivery speed and quality - friction costs multiply at scale",
                        implementation_approach="Value stream mapping, bottleneck analysis, process redesign, ownership clarification",
                        estimated_duration_weeks=8,
                        resource_requirements="Process consultants, cross-functional team time, implementation resources",
                    )
                )

            elif signal.alert_type == "psychological_debt_critical":
                recommendations.append(
                    InterventionRecommendation(
                        title="Capacity & Workload Rebalancing",
                        description="Rebalance workload and add capacity to pay down psychological debt",
                        category=InterventionCategory.WORKLOAD,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="Debt reduction of 20-30 points, improved sustainability",
                        business_rationale="Psychological debt creates compounding interest - addressing it prevents crisis scenarios",
                        implementation_approach="Hiring/contracting, priority reduction, scope adjustment, temporary resource augmentation",
                        estimated_duration_weeks=12,
                        resource_requirements="Hiring budget, contractor resources, priority framework implementation",
                    )
                )

            elif signal.alert_type == "resilience_deficit":
                recommendations.append(
                    InterventionRecommendation(
                        title="Resilience Capacity Building",
                        description="Build organizational resilience through support systems and buffers",
                        category=InterventionCategory.STRUCTURAL,
                        target_encodings=signal.affected_encodings,
                        expected_outcomes="20-30% improvement in resilience capacity, increased adaptability",
                        business_rationale="Resilience determines how well the organization navigates change and stress - critical for long-term sustainability",
                        implementation_approach="Buffer capacity creation, support system investment, adaptation training, learning culture development",
                        estimated_duration_weeks=16,
                        resource_requirements="Significant investment in hiring, training, and support infrastructure",
                    )
                )

        return recommendations

    # ═══════════════════════════════════════════════════════════════
    # HELPER METHODS
    # ═══════════════════════════════════════════════════════════════

    def _determine_trend(self, slope: float, threshold: float = 5.0) -> str:
        """Determine trend direction based on slope."""
        if slope > threshold:
            return "increasing"  # For metrics where higher is worse
        if slope < -threshold:
            return "decreasing"  # For metrics where lower is better
        return "stable"

    def _calculate_acceleration(
        self, historical_values: list[float], current_value: float
    ) -> Optional[float]:
        """Calculate acceleration (change in slope)."""
        if len(historical_values) < 3:
            return None

        # Calculate recent slopes
        slopes = []
        for i in range(1, len(historical_values)):
            slopes.append(historical_values[i] - historical_values[i - 1])

        # Add current slope
        if historical_values:
            slopes.append(current_value - historical_values[-1])

        if len(slopes) < 2:
            return None

        # Acceleration is change in slope
        return slopes[-1] - slopes[-2]

    def _calculate_confidence(self, data_sources: dict[str, Any]) -> float:
        """Calculate confidence in metrics based on data quality."""
        sample_size = data_sources.get("sample_size", 0)
        data_quality = data_sources.get("data_quality", 50)

        # Confidence increases with sample size and data quality
        base_confidence = min(data_quality, 100)

        # Adjust for sample size
        if sample_size > 100:
            sample_factor = 1.0
        elif sample_size > 50:
            sample_factor = 0.9
        elif sample_size > 20:
            sample_factor = 0.75
        else:
            sample_factor = 0.5

        return round(base_confidence * sample_factor, 2)

    def _calculate_communication_load(self, metrics: dict[str, Any]) -> float:
        """Calculate communication load component."""
        volume = metrics.get("daily_message_volume", 100)
        complexity = metrics.get("message_complexity", 50)

        # Normalize and combine
        normalized_volume = min(volume / 200, 1.0) * 100
        return (normalized_volume + complexity) / 2

    def _calculate_meeting_cognitive_cost(self, metrics: dict[str, Any]) -> float:
        """Calculate meeting cognitive cost component."""
        meeting_hours = metrics.get("weekly_meeting_hours", 10)
        attendee_count = metrics.get("avg_meeting_attendees", 5)

        # Cognitive cost increases with meeting time and attendee count
        time_cost = min(meeting_hours / 25, 1.0) * 100
        complexity_cost = min(attendee_count / 15, 1.0) * 100

        return (time_cost + complexity_cost) / 2

    def _calculate_task_switching_cost(self, metrics: dict[str, Any]) -> float:
        """Calculate task switching cost component."""
        context_switches = metrics.get("daily_context_switches", 10)

        # Each switch has cognitive cost
        return min(context_switches / 30, 1.0) * 100

    def _calculate_decision_complexity(self, metrics: dict[str, Any]) -> float:
        """Calculate decision complexity component."""
        decision_frequency = metrics.get("daily_decisions", 20)
        decision_stakes = metrics.get("decision_stakes_score", 50)

        normalized_frequency = min(decision_frequency / 50, 1.0) * 100
        return (normalized_frequency + decision_stakes) / 2

    def _calculate_information_overload(self, metrics: dict[str, Any]) -> float:
        """Calculate information overload component."""
        info_volume = metrics.get("daily_info_items", 100)
        processing_capacity = metrics.get("processing_capacity", 100)

        overload_ratio = info_volume / max(processing_capacity, 1)
        return min(overload_ratio * 50, 100)

    def _calculate_trust_volatility(self, metrics: dict[str, Any]) -> float:
        """Calculate trust volatility (instability)."""
        # Volatility from variance in trust indicators
        trust_variance = metrics.get("trust_variance", 20)
        return min(trust_variance, 100)

    def _identify_volatility_triggers(self, data_sources: dict[str, Any]) -> list[str]:
        """Identify primary volatility triggers."""
        triggers = []

        wellness = data_sources.get("wellness_metrics", {})
        if wellness.get("workload_score", 0) > 70:
            triggers.append("high_workload")
        if wellness.get("after_hours_activity", 0) > 60:
            triggers.append("after_hours_work")

        culture = data_sources.get("culture_metrics", {})
        if culture.get("conflict_level", "low") in ["high", "critical"]:
            triggers.append("elevated_conflict")

        communication = data_sources.get("communication_metrics", {})
        if communication.get("sentiment_variance", 0) > 40:
            triggers.append("sentiment_instability")

        return triggers if triggers else ["general_stress"]

    def _calculate_recovery_time(self, metrics: dict[str, Any]) -> float:
        """Calculate average recovery time from stress events."""
        return metrics.get("avg_recovery_days", 3.0)

    def _calculate_debt_rate(self, metrics: dict[str, Any]) -> float:
        """Calculate rate of debt accumulation per week."""
        return metrics.get("debt_accumulation_rate", 2.5)

    def _calculate_paydown_capacity(self, metrics: dict[str, Any]) -> float:
        """Calculate organization's capacity to pay down debt."""
        return metrics.get("debt_paydown_capacity", 30.0)

    def _calculate_resilience_buffer(self, metrics: dict[str, Any]) -> float:
        """Calculate resilience buffer (margin before crisis)."""
        return metrics.get("resilience_buffer", 40.0)

    def _format_cli_alert(self, cli: EncodingCalculation) -> str:
        """Format CLI alert description."""
        drivers = cli.drivers or {}
        primary = drivers.get("primary_driver", "unknown")
        return (
            f"Cognitive Load Index is at {cli.value:.1f}/100 ({cli.trend} trend). "
            f"Primary driver: {primary}. "
            f"Organization is operating at {'CRITICAL' if cli.value > 85 else 'ELEVATED'} cognitive load levels."
        )

    def _format_tsc_alert(self, tsc: EncodingCalculation) -> str:
        """Format TSC alert description."""
        return (
            f"Trust Stability Curve is at {tsc.value:.1f}/100 ({tsc.trend} trend). "
            f"Trust patterns show {'CRITICAL' if tsc.value < 35 else 'CONCERNING'} erosion signals. "
            f"Immediate attention to transparency and collaboration required."
        )

    def _format_evs_alert(self, evs: EncodingCalculation) -> str:
        """Format EVS alert description."""
        return (
            f"Emotional Volatility Signal is at {evs.value:.1f}/100 ({evs.trend} trend). "
            f"Organization experiencing {'CRITICAL' if evs.value > 80 else 'ELEVATED'} emotional volatility. "
            f"Conflict and stress patterns require structural intervention."
        )

    def _format_cfs_alert(self, cfs: EncodingCalculation) -> str:
        """Format CFS alert description."""
        return (
            f"Coordination Friction Score is at {cfs.value:.1f}/100 ({cfs.trend} trend). "
            f"Significant coordination inefficiencies detected. "
            f"Process optimization and bottleneck removal recommended."
        )

    def _format_pda_alert(self, pda: EncodingCalculation) -> str:
        """Format PDA alert description."""
        return (
            f"Psychological Debt Accumulation is at {pda.value:.1f}/100 ({pda.trend} trend). "
            f"Debt at {'CRITICAL' if pda.value > 85 else 'HIGH'} levels. "
            f"Immediate capacity and workload rebalancing required."
        )

    def _format_rrc_alert(self, rrc: EncodingCalculation) -> str:
        """Format RRC alert description."""
        return (
            f"Recovery & Resilience Capacity is at {rrc.value:.1f}/100 ({rrc.trend} trend). "
            f"Insufficient resilience capacity detected. "
            f"Organization vulnerable to stressors and shocks."
        )
