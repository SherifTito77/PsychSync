"""
Real-time Signal Processing Engine for Radar System
Processes behavioral signals in real-time with ML-based pattern correlation
"""

import asyncio
import logging
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of behavioral signals"""

    TOXICITY = "toxicity"
    BURNOUT = "burnout"
    COMMUNICATION = "communication"
    SENTIMENT = "sentiment"
    CONFLICT = "conflict"
    PSYCHOLOGICAL_SAFETY = "psychological_safety"


@dataclass
class BehavioralSignal:
    """Individual behavioral signal"""

    signal_type: SignalType
    timestamp: datetime
    source: str  # 'assessment', 'communication', 'hris', 'slack', etc.
    severity: float  # 0.0-1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    team_id: Optional[str] = None
    organization_id: str = ""


@dataclass
class PatternCorrelation:
    """Correlated pattern detection result"""

    pattern_id: str
    pattern_type: str
    confidence: float
    signals: List[BehavioralSignal]
    first_seen: datetime
    last_seen: datetime
    severity_trend: str  # 'increasing', 'stable', 'decreasing'
    predicted_risk: float


class RealtimeSignalProcessor:
    """
    Real-time signal processing engine with ML-based pattern correlation

    Features:
    - Sliding window signal analysis
    - Cross-signal pattern correlation
    - Predictive zone migration tracking
    - Automated threshold adaptation
    """

    def __init__(self, window_size_seconds: int = 3600):
        self.window_size_seconds = window_size_seconds
        self.signal_buffer: deque[BehavioralSignal] = deque(maxlen=10000)
        self.pattern_cache: Dict[str, PatternCorrelation] = {}
        self.logger = logging.getLogger(__name__)

        # ML Model placeholders (would be trained in production)
        self.pattern_detector = None  # Would load trained model
        self.risk_predictor = None  # Would load trained model

    async def process_signal(self, signal: BehavioralSignal) -> Dict[str, Any]:
        """
        Process a new behavioral signal and detect patterns

        Returns:
            - Signal processing result
            - Any detected patterns
            - Updated risk predictions
        """
        try:
            # Add to signal buffer
            self.signal_buffer.append(signal)

            # Clean old signals outside window
            await self._clean_old_signals()

            # Analyze for patterns
            detected_patterns = await self._detect_patterns(signal)

            # Update predictions
            risk_prediction = await self._predict_zone_migration()

            # Check for threshold breaches
            alerts = await self._check_thresholds(signal, detected_patterns)

            return {
                "signal_processed": True,
                "signal_id": f"{signal.signal_type.value}_{signal.timestamp.isoformat()}",
                "detected_patterns": [
                    self._serialize_pattern(p) for p in detected_patterns
                ],
                "risk_prediction": risk_prediction,
                "alerts": alerts,
                "processing_time_ms": 0,  # Would track actual time
            }

        except Exception as e:
            self.logger.error(f"Failed to process signal: {e}", exc_info=True)
            return {
                "signal_processed": False,
                "error": str(e),
            }

    async def _clean_old_signals(self) -> None:
        """Remove signals outside the time window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=self.window_size_seconds)

        # Filter signals in-place
        self.signal_buffer = deque(
            (s for s in self.signal_buffer if s.timestamp >= cutoff_time),
            maxlen=self.signal_buffer.maxlen,
        )

    async def _detect_patterns(
        self, new_signal: BehavioralSignal
    ) -> List[PatternCorrelation]:
        """
        Detect patterns across multiple signals using ML correlation

        Pattern types:
        1. Escalation: Severity increasing over time
        2. Cross-source: Same signal type from multiple sources
        3. Cluster: Geographic or team-based clustering
        4. Temporal: Time-based patterns (e.g., end-of-week spikes)
        """
        patterns = []

        try:
            # Get recent signals of same type
            recent_signals = [
                s
                for s in self.signal_buffer
                if s.signal_type == new_signal.signal_type
                and s.organization_id == new_signal.organization_id
            ]

            if len(recent_signals) < 3:
                return patterns  # Not enough data

            # Pattern 1: Escalation Detection
            escalation_pattern = await self._detect_escalation(recent_signals)
            if escalation_pattern:
                patterns.append(escalation_pattern)

            # Pattern 2: Cross-Source Correlation
            cross_source_pattern = await self._detect_cross_source_correlation(
                recent_signals
            )
            if cross_source_pattern:
                patterns.append(cross_source_pattern)

            # Pattern 3: Temporal Pattern (e.g., weekly cycles)
            temporal_pattern = await self._detect_temporal_patterns(recent_signals)
            if temporal_pattern:
                patterns.append(temporal_pattern)

            # Pattern 4: Cluster Detection (team-based)
            cluster_pattern = await self._detect_team_clusters(recent_signals)
            if cluster_pattern:
                patterns.append(cluster_pattern)

            return patterns

        except Exception as e:
            self.logger.error(f"Pattern detection failed: {e}", exc_info=True)
            return patterns

    async def _detect_escalation(
        self, signals: List[BehavioralSignal]
    ) -> Optional[PatternCorrelation]:
        """Detect escalating severity patterns"""
        if len(signals) < 5:
            return None

        # Sort by timestamp
        sorted_signals = sorted(signals, key=lambda s: s.timestamp)

        # Calculate trend
        recent_severity = sum(s.severity for s in sorted_signals[-3:]) / 3
        earlier_severity = sum(s.severity for s in sorted_signals[:3]) / 3

        if recent_severity > earlier_severity * 1.3:  # 30% increase
            trend = "increasing"
        elif recent_severity < earlier_severity * 0.7:  # 30% decrease
            trend = "decreasing"
        else:
            trend = "stable"

        if trend == "increasing" and recent_severity > 0.5:
            return PatternCorrelation(
                pattern_id=f"escalation_{datetime.utcnow().isoformat()}",
                pattern_type="escalation",
                confidence=min(1.0, (recent_severity - earlier_severity) * 2),
                signals=sorted_signals[-5:],
                first_seen=sorted_signals[0].timestamp,
                last_seen=sorted_signals[-1].timestamp,
                severity_trend=trend,
                predicted_risk=min(1.0, recent_severity + 0.2),
            )

        return None

    async def _detect_cross_source_correlation(
        self, signals: List[BehavioralSignal]
    ) -> Optional[PatternCorrelation]:
        """Detect when same signal type appears from multiple sources"""
        sources = set(s.source for s in signals)

        if len(sources) >= 3:  # Signal from 3+ different sources
            # Calculate average severity across sources
            avg_severity = sum(s.severity for s in signals) / len(signals)

            return PatternCorrelation(
                pattern_id=f"cross_source_{datetime.utcnow().isoformat()}",
                pattern_type="cross_source_correlation",
                confidence=min(
                    1.0, len(sources) / 5.0
                ),  # More sources = higher confidence
                signals=signals[-10:],
                first_seen=signals[0].timestamp,
                last_seen=signals[-1].timestamp,
                severity_trend="stable",
                predicted_risk=avg_severity,
            )

        return None

    async def _detect_temporal_patterns(
        self, signals: List[BehavioralSignal]
    ) -> Optional[PatternCorrelation]:
        """Detect temporal patterns (e.g., day of week, time of day)"""
        if len(signals) < 10:
            return None

        # Group by day of week
        dow_counts = {}
        for s in signals:
            dow = s.timestamp.weekday()
            dow_counts[dow] = dow_counts.get(dow, 0) + 1

        # Check for concentration on specific days
        total = len(signals)
        max_dow_count = max(dow_counts.values())

        if max_dow_count / total > 0.5:  # More than 50% on one day
            dow_with_max = max(dow_counts, key=dow_counts.get)
            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

            return PatternCorrelation(
                pattern_id=f"temporal_{datetime.utcnow().isoformat()}",
                pattern_type="temporal_pattern",
                confidence=max_dow_count / total,
                signals=signals,
                first_seen=signals[0].timestamp,
                last_seen=signals[-1].timestamp,
                severity_trend="stable",
                predicted_risk=sum(s.severity for s in signals) / total,
            )

        return None

    async def _detect_team_clusters(
        self, signals: List[BehavioralSignal]
    ) -> Optional[PatternCorrelation]:
        """Detect team-based clustering of issues"""
        if not signals[0].team_id:
            return None

        # Group by team
        team_signals = {}
        for s in signals:
            if s.team_id:
                if s.team_id not in team_signals:
                    team_signals[s.team_id] = []
                team_signals[s.team_id].append(s)

        # Check if one team has significantly more signals
        if len(team_signals) < 2:
            return None

        team_counts = {tid: len(sigs) for tid, sigs in team_signals.items()}
        max_count = max(team_counts.values())

        if max_count > 5:  # Team with 5+ signals
            team_with_max = max(team_counts, key=team_counts.get)
            avg_severity = sum(s.severity for s in team_signals[team_with_max]) / len(
                team_signals[team_with_max]
            )

            return PatternCorrelation(
                pattern_id=f"cluster_{datetime.utcnow().isoformat()}",
                pattern_type="team_cluster",
                confidence=min(1.0, max_count / 10.0),
                signals=team_signals[team_with_max][-10:],
                first_seen=team_signals[team_with_max][0].timestamp,
                last_seen=team_signals[team_with_max][-1].timestamp,
                severity_trend="stable",
                predicted_risk=avg_severity,
            )

        return None

    async def _predict_zone_migration(self) -> Dict[str, Any]:
        """
        Predict zone migration using ML model

        Returns:
            - Current zone
            - Predicted zone (7 days, 14 days, 30 days)
            - Confidence levels
            - Contributing factors
        """
        try:
            # Get recent signals
            recent_signals = list(self.signal_buffer)

            if len(recent_signals) < 10:
                return {
                    "current_zone": "unknown",
                    "predictions": [],
                    "insufficient_data": True,
                }

            # Calculate current aggregate risk
            current_risk = sum(s.severity for s in recent_signals[-50:]) / min(
                50, len(recent_signals)
            )

            # Simple trend-based prediction (would use ML model in production)
            predictions = []

            # 7-day prediction
            risk_7d = current_risk * 1.1  # Assume 10% increase
            zone_7d = self._risk_to_zone(risk_7d)
            predictions.append(
                {
                    "horizon_days": 7,
                    "predicted_zone": zone_7d,
                    "predicted_risk": risk_7d,
                    "confidence": 0.65,
                }
            )

            # 14-day prediction
            risk_14d = current_risk * 1.2  # Assume 20% increase
            zone_14d = self._risk_to_zone(risk_14d)
            predictions.append(
                {
                    "horizon_days": 14,
                    "predicted_zone": zone_14d,
                    "predicted_risk": risk_14d,
                    "confidence": 0.55,
                }
            )

            # 30-day prediction
            risk_30d = current_risk * 1.3  # Assume 30% increase
            zone_30d = self._risk_to_zone(risk_30d)
            predictions.append(
                {
                    "horizon_days": 30,
                    "predicted_zone": zone_30d,
                    "predicted_risk": risk_30d,
                    "confidence": 0.45,
                }
            )

            return {
                "current_zone": self._risk_to_zone(current_risk),
                "current_risk": current_risk,
                "predictions": predictions,
                "insufficient_data": False,
            }

        except Exception as e:
            self.logger.error(f"Zone migration prediction failed: {e}", exc_info=True)
            return {
                "current_zone": "unknown",
                "predictions": [],
                "error": str(e),
            }

    def _risk_to_zone(self, risk: float) -> str:
        """Convert risk score to zone"""
        if risk >= 0.6:
            return "red"
        elif risk >= 0.3:
            return "yellow"
        else:
            return "green"

    async def _check_thresholds(
        self, signal: BehavioralSignal, patterns: List[PatternCorrelation]
    ) -> List[Dict[str, Any]]:
        """Check for threshold breaches and generate alerts"""
        alerts = []

        # Check individual signal severity
        if signal.severity >= 0.8:
            alerts.append(
                {
                    "alert_type": "critical_signal",
                    "severity": "critical",
                    "message": f"Critical {signal.signal_type.value} signal detected",
                    "signal": self._serialize_signal(signal),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        elif signal.severity >= 0.6:
            alerts.append(
                {
                    "alert_type": "high_severity_signal",
                    "severity": "high",
                    "message": f"High severity {signal.signal_type.value} signal detected",
                    "signal": self._serialize_signal(signal),
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )

        # Check for high-confidence patterns
        for pattern in patterns:
            if pattern.confidence >= 0.8:
                alerts.append(
                    {
                        "alert_type": "high_confidence_pattern",
                        "severity": "high",
                        "message": f"High confidence {pattern.pattern_type} pattern detected",
                        "pattern": self._serialize_pattern(pattern),
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )

        return alerts

    def _serialize_signal(self, signal: BehavioralSignal) -> Dict[str, Any]:
        """Serialize signal for JSON response"""
        return {
            "signal_type": signal.signal_type.value,
            "timestamp": signal.timestamp.isoformat(),
            "source": signal.source,
            "severity": signal.severity,
            "metadata": signal.metadata,
            "user_id": signal.user_id,
            "team_id": signal.team_id,
            "organization_id": signal.organization_id,
        }

    def _serialize_pattern(self, pattern: PatternCorrelation) -> Dict[str, Any]:
        """Serialize pattern for JSON response"""
        return {
            "pattern_id": pattern.pattern_id,
            "pattern_type": pattern.pattern_type,
            "confidence": pattern.confidence,
            "signal_count": len(pattern.signals),
            "first_seen": pattern.first_seen.isoformat(),
            "last_seen": pattern.last_seen.isoformat(),
            "severity_trend": pattern.severity_trend,
            "predicted_risk": pattern.predicted_risk,
        }


# Singleton instance
realtime_signal_processor = RealtimeSignalProcessor()
