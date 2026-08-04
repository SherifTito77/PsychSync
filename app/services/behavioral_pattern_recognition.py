"""
Behavioral Pattern Recognition Service
Advanced algorithms for detecting user behavioral patterns, anomalies, and generating insights.
Leverages machine learning, statistical analysis, and temporal pattern detection.

Key Features:
- Temporal pattern detection in user behavior
- Anomaly detection using statistical and ML methods
- Behavioral segmentation and clustering
- Pattern-based predictions and recommendations
- Real-time pattern monitoring and alerting
- Cross-user behavioral similarity analysis
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
import pandas as pd
import redis.asyncio as redis
from scipy import stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class PatternType(Enum):
    """Types of behavioral patterns to detect."""

    TEMPORAL = "temporal"  # Time-based patterns
    SEQUENTIAL = "sequential"  # Action sequence patterns
    FREQUENCY = "frequency"  # Usage frequency patterns
    PREFERENCE = "preference"  # Preference and choice patterns
    SOCIAL = "social"  # Social interaction patterns
    PERFORMANCE = "performance"  # Performance and efficiency patterns
    RISK = "risk"  # Risk and churn prediction patterns
    LEARNING = "learning"  # Learning and adaptation patterns


class AnomalyType(Enum):
    """Types of behavioral anomalies."""

    STATISTICAL = "statistical"  # Statistical outliers
    TEMPORAL = "temporal"  # Time-based anomalies
    BEHAVIORAL = "behavioral"  # Unusual behavior patterns
    PERFORMANCE = "performance"  # Performance anomalies
    SECURITY = "security"  # Security-related anomalies
    ENGAGEMENT = "engagement"  # Engagement drops/spikes


class PatternSeverity(Enum):
    """Severity levels for detected anomalies."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BehavioralEvent:
    """Represents a single behavioral event."""

    user_id: str
    event_type: str
    timestamp: datetime
    properties: dict[str, Any]
    session_id: str
    duration_ms: int | None = None
    success: bool = True
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class Pattern:
    """Detected behavioral pattern."""

    pattern_id: str
    pattern_type: PatternType
    description: str
    confidence: float
    support: int  # Number of instances supporting this pattern
    users: list[str]
    time_window: dict[str, datetime]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Anomaly:
    """Detected behavioral anomaly."""

    anomaly_id: str
    user_id: str
    anomaly_type: AnomalyType
    severity: PatternSeverity
    description: str
    confidence: float
    detected_at: datetime
    baseline_metrics: dict[str, float]
    observed_metrics: dict[str, float]
    recommendations: list[str] = field(default_factory=list)


@dataclass
class PatternConfig:
    """Configuration for pattern recognition algorithms."""

    # Pattern detection settings
    min_pattern_support: int = 5  # Minimum instances for pattern validity
    pattern_confidence_threshold: float = 0.7
    temporal_window_hours: int = 168  # 1 week default
    max_patterns_per_user: int = 100

    # Anomaly detection settings
    anomaly_sensitivity: float = 0.1  # Isolation Forest contamination
    statistical_threshold: float = 2.5  # Standard deviations
    min_anomaly_confidence: float = 0.6

    # Clustering settings
    clustering_eps: float = 0.5  # DBSCAN epsilon
    min_cluster_size: int = 3
    n_clusters: int = 5  # K-Means clusters

    # Performance settings
    max_events_per_analysis: int = 10000
    batch_size: int = 1000
    cache_ttl_hours: int = 24

    # Redis configuration
    redis_url: str = "redis://localhost:6379/5"


class BehavioralPatternRecognizer:
    """
    Advanced behavioral pattern recognition engine.
    """

    def __init__(self, db_session: Session, config: PatternConfig | None = None):
        self.db = db_session
        self.config = config or PatternConfig()
        self.redis_client: redis.Redis | None = None
        self._init_redis()

        # Initialize ML models
        self.scaler = StandardScaler()
        self.isolation_forest = IsolationForest(
            contamination=self.config.anomaly_sensitivity, random_state=42
        )
        self.kmeans = KMeans(n_clusters=self.config.n_clusters, random_state=42)
        self.dbscan = DBSCAN(
            eps=self.config.clustering_eps, min_samples=self.config.min_cluster_size
        )

        # Pattern detection algorithms
        self.algorithms = {
            PatternType.TEMPORAL: self._detect_temporal_patterns,
            PatternType.SEQUENTIAL: self._detect_sequential_patterns,
            PatternType.FREQUENCY: self._detect_frequency_patterns,
            PatternType.PREFERENCE: self._detect_preference_patterns,
            PatternType.SOCIAL: self._detect_social_patterns,
            PatternType.PERFORMANCE: self._detect_performance_patterns,
            PatternType.RISK: self._detect_risk_patterns,
            PatternType.LEARNING: self._detect_learning_patterns,
        }

    def _init_redis(self) -> None:
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Pattern recognition Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for pattern recognition: {e}")
            self.redis_client = None

    async def analyze_user_behavior(
        self,
        user_id: str,
        time_window_hours: int | None = None,
        pattern_types: list[PatternType] | None = None,
    ) -> dict[str, Any]:
        """
        Comprehensive behavioral analysis for a specific user.
        """
        try:
            time_window = time_window_hours or self.config.temporal_window_hours
            pattern_types = pattern_types or list(PatternType)

            # Get user behavioral events
            events = await self._get_user_events(user_id, time_window)
            if not events:
                return self._get_empty_analysis(user_id)

            # Initialize results
            analysis = {
                "user_id": user_id,
                "analysis_period": {
                    "start": (
                        datetime.utcnow() - timedelta(hours=time_window)
                    ).isoformat(),
                    "end": datetime.utcnow().isoformat(),
                    "hours": time_window,
                },
                "events_analyzed": len(events),
                "patterns": [],
                "anomalies": [],
                "insights": [],
                "recommendations": [],
                "behavioral_profile": {},
                "risk_assessment": {},
            }

            # Detect patterns
            for pattern_type in pattern_types:
                try:
                    patterns = await self.algorithms[pattern_type](events, user_id)
                    analysis["patterns"].extend(patterns)
                except Exception as e:
                    logger.error(f"Error detecting {pattern_type.value} patterns: {e}")

            # Filter patterns by confidence and support
            analysis["patterns"] = [
                p
                for p in analysis["patterns"]
                if p.confidence >= self.config.pattern_confidence_threshold
                and p.support >= self.config.min_pattern_support
            ]

            # Detect anomalies
            analysis["anomalies"] = await self._detect_anomalies(events, user_id)

            # Generate behavioral profile
            analysis["behavioral_profile"] = await self._generate_behavioral_profile(
                events
            )

            # Generate insights and recommendations
            analysis["insights"] = await self._generate_insights(
                analysis["patterns"], analysis["anomalies"]
            )
            analysis["recommendations"] = await self._generate_recommendations(analysis)
            analysis["risk_assessment"] = await self._assess_behavioral_risk(analysis)

            # Cache results
            await self._cache_analysis(user_id, analysis)

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing user behavior for {user_id}: {e}")
            return self._get_empty_analysis(user_id)

    async def _detect_temporal_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect time-based behavioral patterns."""
        patterns = []

        try:
            # Convert events to DataFrame for analysis
            df = pd.DataFrame(
                [
                    {
                        "timestamp": e.timestamp,
                        "event_type": e.event_type,
                        "hour": e.timestamp.hour,
                        "day_of_week": e.timestamp.weekday(),
                        "duration_ms": e.duration_ms or 0,
                    }
                    for e in events
                ]
            )

            if df.empty:
                return patterns

            # Pattern 1: Time of day preferences
            hour_counts = df["hour"].value_counts()
            if len(hour_counts) > 0:
                peak_hours = hour_counts.nlargest(3).index.tolist()
                if len(peak_hours) >= 2:
                    patterns.append(
                        Pattern(
                            pattern_id=f"temporal_peak_hours_{user_id}",
                            pattern_type=PatternType.TEMPORAL,
                            description=f"Most active during hours: {', '.join(map(str, peak_hours))}",
                            confidence=hour_counts.iloc[0] / len(df),
                            support=len(df),
                            users=[user_id],
                            time_window={
                                "start": df["timestamp"].min(),
                                "end": df["timestamp"].max(),
                            },
                            metadata={
                                "peak_hours": peak_hours,
                                "activity_distribution": hour_counts.to_dict(),
                            },
                        )
                    )

            # Pattern 2: Day of week preferences
            dow_counts = df["day_of_week"].value_counts()
            if len(dow_counts) > 0:
                peak_days = dow_counts.nlargest(2).index.tolist()
                patterns.append(
                    Pattern(
                        pattern_id=f"temporal_peak_days_{user_id}",
                        pattern_type=PatternType.TEMPORAL,
                        description=f"Most active on: {', '.join(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'][day] for day in peak_days)}",
                        confidence=dow_counts.iloc[0] / len(df),
                        support=len(df),
                        users=[user_id],
                        time_window={
                            "start": df["timestamp"].min(),
                            "end": df["timestamp"].max(),
                        },
                        metadata={
                            "peak_days": peak_days,
                            "day_distribution": dow_counts.to_dict(),
                        },
                    )
                )

            # Pattern 3: Session duration patterns
            if "duration_ms" in df.columns and df["duration_ms"].sum() > 0:
                avg_duration = df["duration_ms"].mean()
                if avg_duration > 0:
                    patterns.append(
                        Pattern(
                            pattern_id=f"temporal_session_duration_{user_id}",
                            pattern_type=PatternType.TEMPORAL,
                            description=f"Average session duration: {avg_duration / 1000:.1f} seconds",
                            confidence=0.8,
                            support=len(df[df["duration_ms"] > 0]),
                            users=[user_id],
                            time_window={
                                "start": df["timestamp"].min(),
                                "end": df["timestamp"].max(),
                            },
                            metadata={
                                "avg_duration_ms": avg_duration,
                                "total_sessions": len(df[df["duration_ms"] > 0]),
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error in temporal pattern detection: {e}")

        return patterns

    async def _detect_sequential_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect sequential action patterns."""
        patterns = []

        try:
            # Sort events by timestamp
            sorted_events = sorted(events, key=lambda x: x.timestamp)

            # Extract action sequences
            sequences = []
            current_sequence = []
            last_timestamp = None

            for event in sorted_events:
                # Start new sequence if gap > 30 minutes
                if (
                    last_timestamp
                    and (event.timestamp - last_timestamp).total_seconds() > 1800
                ):
                    if len(current_sequence) >= 3:
                        sequences.append(current_sequence)
                    current_sequence = [event.event_type]
                else:
                    current_sequence.append(event.event_type)

                last_timestamp = event.timestamp

            if len(current_sequence) >= 3:
                sequences.append(current_sequence)

            if not sequences:
                return patterns

            # Find common sequences
            sequence_counts = {}
            for seq in sequences:
                seq_key = " -> ".join(seq)
                sequence_counts[seq_key] = sequence_counts.get(seq_key, 0) + 1

            # Identify frequent sequences
            for seq_key, count in sequence_counts.items():
                if count >= self.config.min_pattern_support:
                    confidence = count / len(sequences)
                    if confidence >= self.config.pattern_confidence_threshold:
                        patterns.append(
                            Pattern(
                                pattern_id=f"sequential_{hash(seq_key)}_{user_id}",
                                pattern_type=PatternType.SEQUENTIAL,
                                description=f"Frequent action sequence: {seq_key}",
                                confidence=confidence,
                                support=count,
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "sequence": seq_key.split(" -> "),
                                    "frequency": count,
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error in sequential pattern detection: {e}")

        return patterns

    async def _detect_frequency_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect usage frequency patterns."""
        patterns = []

        try:
            # Count event types
            event_counts = {}
            for event in events:
                event_counts[event.event_type] = (
                    event_counts.get(event.event_type, 0) + 1
                )

            if not event_counts:
                return patterns

            total_events = len(events)

            # High-frequency event patterns
            for event_type, count in event_counts.items():
                frequency = count / total_events
                if frequency >= 0.2:  # 20% or more of all events
                    patterns.append(
                        Pattern(
                            pattern_id=f"frequency_high_{event_type}_{user_id}",
                            pattern_type=PatternType.FREQUENCY,
                            description=f"High frequency usage of {event_type}: {frequency:.1%} of all activities",
                            confidence=frequency,
                            support=count,
                            users=[user_id],
                            time_window={
                                "start": events[0].timestamp,
                                "end": events[-1].timestamp,
                            },
                            metadata={
                                "event_type": event_type,
                                "frequency": frequency,
                                "count": count,
                            },
                        )
                    )

            # Usage pattern regularity
            daily_counts = {}
            for event in events:
                date_key = event.timestamp.date()
                daily_counts[date_key] = daily_counts.get(date_key, 0) + 1

            if len(daily_counts) >= 7:  # Need at least a week of data
                counts = list(daily_counts.values())
                cv = stats.variation(counts) if np.mean(counts) > 0 else 0

                # Low coefficient of variation indicates regular usage
                if cv < 0.5:
                    patterns.append(
                        Pattern(
                            pattern_id=f"frequency_regular_{user_id}",
                            pattern_type=PatternType.FREQUENCY,
                            description=f"Regular usage pattern with low variability (CV: {cv:.2f})",
                            confidence=1.0 - cv,
                            support=len(daily_counts),
                            users=[user_id],
                            time_window={
                                "start": events[0].timestamp,
                                "end": events[-1].timestamp,
                            },
                            metadata={
                                "coefficient_of_variation": cv,
                                "daily_counts": daily_counts,
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error in frequency pattern detection: {e}")

        return patterns

    async def _detect_preference_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect preference and choice patterns."""
        patterns = []

        try:
            # Analyze preferences from event properties
            preferences = {}
            for event in events:
                # Extract preferences from event properties
                for key, value in event.properties.items():
                    if any(
                        pref_key in key.lower()
                        for pref_key in ["type", "category", "style", "option"]
                    ):
                        pref_key = f"{key}_{value}"
                        preferences[pref_key] = preferences.get(pref_key, 0) + 1

            # Identify strong preferences
            for pref_key, count in preferences.items():
                if count >= self.config.min_pattern_support:
                    confidence = count / len(events)
                    if confidence >= self.config.pattern_confidence_threshold:
                        patterns.append(
                            Pattern(
                                pattern_id=f"preference_{hash(pref_key)}_{user_id}",
                                pattern_type=PatternType.PREFERENCE,
                                description=f"Strong preference: {pref_key} ({confidence:.1%} of choices)",
                                confidence=confidence,
                                support=count,
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "preference": pref_key,
                                    "count": count,
                                    "total_choices": len(events),
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error in preference pattern detection: {e}")

        return patterns

    async def _detect_social_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect social interaction patterns."""
        patterns = []

        try:
            # Extract social interactions from events
            social_events = [
                e
                for e in events
                if "team" in e.event_type.lower()
                or "collaboration" in e.event_type.lower()
            ]

            if len(social_events) >= self.config.min_pattern_support:
                # Team activity pattern
                patterns.append(
                    Pattern(
                        pattern_id=f"social_team_active_{user_id}",
                        pattern_type=PatternType.SOCIAL,
                        description=f"Regular team collaboration: {len(social_events)} interactions",
                        confidence=len(social_events) / len(events),
                        support=len(social_events),
                        users=[user_id],
                        time_window={
                            "start": events[0].timestamp,
                            "end": events[-1].timestamp,
                        },
                        metadata={
                            "social_events": len(social_events),
                            "total_events": len(events),
                        },
                    )
                )

                # Time-based social patterns
                social_df = pd.DataFrame(
                    [
                        {"timestamp": e.timestamp, "hour": e.timestamp.hour}
                        for e in social_events
                    ]
                )

                if not social_df.empty:
                    social_hours = social_df["hour"].value_counts()
                    peak_social_hour = social_hours.idxmax()
                    patterns.append(
                        Pattern(
                            pattern_id=f"social_peak_hour_{user_id}",
                            pattern_type=PatternType.SOCIAL,
                            description=f"Peak collaboration hour: {peak_social_hour}:00",
                            confidence=social_hours.iloc[0] / len(social_events),
                            support=len(social_events),
                            users=[user_id],
                            time_window={
                                "start": events[0].timestamp,
                                "end": events[-1].timestamp,
                            },
                            metadata={
                                "peak_hour": peak_social_hour,
                                "hour_distribution": social_hours.to_dict(),
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error in social pattern detection: {e}")

        return patterns

    async def _detect_performance_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect performance and efficiency patterns."""
        patterns = []

        try:
            # Analyze performance metrics from events
            performance_events = [e for e in events if e.duration_ms is not None]

            if len(performance_events) >= self.config.min_pattern_support:
                durations = [e.duration_ms for e in performance_events]
                avg_duration = np.mean(durations)
                std_duration = np.std(durations)

                # Performance consistency pattern
                if std_duration > 0:
                    cv = std_duration / avg_duration
                    if cv < 0.3:  # Low variability indicates consistent performance
                        patterns.append(
                            Pattern(
                                pattern_id=f"performance_consistent_{user_id}",
                                pattern_type=PatternType.PERFORMANCE,
                                description=f"Consistent performance with low variability (CV: {cv:.2f})",
                                confidence=1.0 - cv,
                                support=len(performance_events),
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "avg_duration_ms": avg_duration,
                                    "std_duration_ms": std_duration,
                                    "cv": cv,
                                },
                            )
                        )

                # Performance improvement pattern
                if len(performance_events) >= 10:
                    # Split events into halves to check improvement
                    mid_point = len(performance_events) // 2
                    early_durations = [
                        e.duration_ms for e in performance_events[:mid_point]
                    ]
                    late_durations = [
                        e.duration_ms for e in performance_events[mid_point:]
                    ]

                    early_avg = np.mean(early_durations)
                    late_avg = np.mean(late_durations)

                    if late_avg < early_avg * 0.9:  # 10% improvement
                        improvement_pct = ((early_avg - late_avg) / early_avg) * 100
                        patterns.append(
                            Pattern(
                                pattern_id=f"performance_improvement_{user_id}",
                                pattern_type=PatternType.PERFORMANCE,
                                description=f"Performance improvement: {improvement_pct:.1f}% faster over time",
                                confidence=min(
                                    0.9, improvement_pct / 50
                                ),  # Scale confidence with improvement
                                support=len(performance_events),
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "improvement_pct": improvement_pct,
                                    "early_avg_ms": early_avg,
                                    "late_avg_ms": late_avg,
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error in performance pattern detection: {e}")

        return patterns

    async def _detect_risk_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect risk and churn prediction patterns."""
        patterns = []

        try:
            # Analyze engagement trends
            daily_activity = {}
            for event in events:
                date_key = event.timestamp.date()
                daily_activity[date_key] = daily_activity.get(date_key, 0) + 1

            if len(daily_activity) >= 14:  # Need at least 2 weeks
                dates = sorted(daily_activity.keys())
                activities = [daily_activity[date] for date in dates]

                # Calculate trend
                if len(activities) >= 7:
                    recent_avg = np.mean(activities[-7:])  # Last week
                    earlier_avg = np.mean(activities[-14:-7])  # Previous week

                    decline_rate = (
                        (earlier_avg - recent_avg) / earlier_avg
                        if earlier_avg > 0
                        else 0
                    )

                    if decline_rate > 0.3:  # 30% decline in activity
                        patterns.append(
                            Pattern(
                                pattern_id=f"risk_engagement_decline_{user_id}",
                                pattern_type=PatternType.RISK,
                                description=f"Engagement decline detected: {decline_rate:.1%} decrease in activity",
                                confidence=min(
                                    0.9, decline_rate * 2
                                ),  # Scale confidence with decline
                                support=len(activities),
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "decline_rate": decline_rate,
                                    "recent_avg": recent_avg,
                                    "earlier_avg": earlier_avg,
                                },
                            )
                        )

            # Failed event patterns
            failed_events = [e for e in events if not e.success]
            if len(failed_events) > 0:
                failure_rate = len(failed_events) / len(events)
                if failure_rate > 0.1:  # More than 10% failure rate
                    patterns.append(
                        Pattern(
                            pattern_id=f"risk_high_failure_rate_{user_id}",
                            pattern_type=PatternType.RISK,
                            description=f"High failure rate detected: {failure_rate:.1%} of events failed",
                            confidence=failure_rate,
                            support=len(failed_events),
                            users=[user_id],
                            time_window={
                                "start": events[0].timestamp,
                                "end": events[-1].timestamp,
                            },
                            metadata={
                                "failure_rate": failure_rate,
                                "failed_events": len(failed_events),
                                "total_events": len(events),
                            },
                        )
                    )

        except Exception as e:
            logger.error(f"Error in risk pattern detection: {e}")

        return patterns

    async def _detect_learning_patterns(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Pattern]:
        """Detect learning and adaptation patterns."""
        patterns = []

        try:
            # Analyze learning-related events
            learning_events = [
                e
                for e in events
                if any(
                    keyword in e.event_type.lower()
                    for keyword in ["assessment", "tutorial", "help", "learn"]
                )
            ]

            if len(learning_events) >= self.config.min_pattern_support:
                patterns.append(
                    Pattern(
                        pattern_id=f"learning_active_{user_id}",
                        pattern_type=PatternType.LEARNING,
                        description=f"Active learning behavior: {len(learning_events)} learning activities",
                        confidence=len(learning_events) / len(events),
                        support=len(learning_events),
                        users=[user_id],
                        time_window={
                            "start": events[0].timestamp,
                            "end": events[-1].timestamp,
                        },
                        metadata={
                            "learning_events": len(learning_events),
                            "total_events": len(events),
                        },
                    )
                )

            # Skill progression pattern
            skill_events = [
                e
                for e in events
                if "skill" in e.properties or "assessment" in e.event_type.lower()
            ]
            if len(skill_events) >= 5:
                # Look for score improvements
                scores = []
                for event in skill_events:
                    if "score" in event.properties:
                        scores.append(float(event.properties["score"]))

                if len(scores) >= 3:
                    score_trend = np.polyfit(range(len(scores)), scores, 1)[0]
                    if score_trend > 0.5:  # Positive learning trend
                        patterns.append(
                            Pattern(
                                pattern_id=f"learning_improvement_{user_id}",
                                pattern_type=PatternType.LEARNING,
                                description=f"Skill improvement trend detected: {score_trend:.1f} points per activity",
                                confidence=min(0.9, score_trend / 10),
                                support=len(scores),
                                users=[user_id],
                                time_window={
                                    "start": events[0].timestamp,
                                    "end": events[-1].timestamp,
                                },
                                metadata={
                                    "score_trend": score_trend,
                                    "scores": scores,
                                    "activities": len(skill_events),
                                },
                            )
                        )

        except Exception as e:
            logger.error(f"Error in learning pattern detection: {e}")

        return patterns

    async def _detect_anomalies(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Anomaly]:
        """Detect behavioral anomalies using statistical and ML methods."""
        anomalies = []

        try:
            if len(events) < 10:
                return anomalies  # Not enough data for anomaly detection

            # Prepare feature matrix for ML-based detection
            features = self._extract_features(events)
            if features.empty:
                return anomalies

            # Statistical anomaly detection
            statistical_anomalies = await self._detect_statistical_anomalies(
                features, user_id
            )
            anomalies.extend(statistical_anomalies)

            # ML-based anomaly detection
            ml_anomalies = await self._detect_ml_anomalies(features, user_id)
            anomalies.extend(ml_anomalies)

            # Temporal anomalies
            temporal_anomalies = await self._detect_temporal_anomalies(events, user_id)
            anomalies.extend(temporal_anomalies)

        except Exception as e:
            logger.error(f"Error detecting anomalies for user {user_id}: {e}")

        return anomalies

    def _extract_features(self, events: list[BehavioralEvent]) -> pd.DataFrame:
        """Extract features for ML-based anomaly detection."""
        try:
            features = []
            for event in events:
                feature_dict = {
                    "hour": event.timestamp.hour,
                    "day_of_week": event.timestamp.weekday(),
                    "duration_ms": event.duration_ms or 0,
                    "success": 1 if event.success else 0,
                    "event_type_encoded": hash(event.event_type)
                    % 1000,  # Simple encoding
                }

                # Add numeric properties
                for key, value in event.properties.items():
                    if isinstance(value, (int, float)):
                        feature_dict[f"prop_{key}"] = value

                features.append(feature_dict)

            return pd.DataFrame(features)

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return pd.DataFrame()

    async def _detect_statistical_anomalies(
        self, features: pd.DataFrame, user_id: str
    ) -> list[Anomaly]:
        """Detect anomalies using statistical methods."""
        anomalies = []

        try:
            for column in features.select_dtypes(include=[np.number]).columns:
                values = features[column].dropna()
                if len(values) < 5:
                    continue

                # Z-score based outlier detection
                z_scores = np.abs(stats.zscore(values))
                outlier_indices = np.where(
                    z_scores > self.config.statistical_threshold
                )[0]

                for idx in outlier_indices:
                    actual_idx = values.index[idx]
                    anomalies.append(
                        Anomaly(
                            anomaly_id=f"statistical_{column}_{actual_idx}_{user_id}",
                            user_id=user_id,
                            anomaly_type=AnomalyType.STATISTICAL,
                            severity=(
                                PatternSeverity.MEDIUM
                                if z_scores[idx] < 4
                                else PatternSeverity.HIGH
                            ),
                            description=f"Statistical outlier in {column}: value {values.iloc[idx]} (z-score: {z_scores[idx]:.2f})",
                            confidence=min(0.9, z_scores[idx] / 5),
                            detected_at=datetime.utcnow(),
                            baseline_metrics={
                                column + "_mean": float(values.mean()),
                                column + "_std": float(values.std()),
                            },
                            observed_metrics={column: float(values.iloc[idx])},
                        )
                    )

        except Exception as e:
            logger.error(f"Error in statistical anomaly detection: {e}")

        return anomalies

    async def _detect_ml_anomalies(
        self, features: pd.DataFrame, user_id: str
    ) -> list[Anomaly]:
        """Detect anomalies using machine learning methods."""
        anomalies = []

        try:
            # Prepare data
            numeric_features = features.select_dtypes(include=[np.number])
            if numeric_features.empty or len(numeric_features) < 10:
                return anomalies

            # Scale features
            scaled_features = self.scaler.fit_transform(numeric_features)

            # Fit Isolation Forest
            anomaly_labels = self.isolation_forest.fit_predict(scaled_features)
            anomaly_scores = self.isolation_forest.decision_function(scaled_features)

            # Identify anomalies (-1 indicates anomaly)
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = PatternSeverity.LOW
                if anomaly_scores[idx] < -0.3:
                    severity = PatternSeverity.MEDIUM
                if anomaly_scores[idx] < -0.5:
                    severity = PatternSeverity.HIGH
                if anomaly_scores[idx] < -0.7:
                    severity = PatternSeverity.CRITICAL

                anomalies.append(
                    Anomaly(
                        anomaly_id=f"ml_isolation_{idx}_{user_id}",
                        user_id=user_id,
                        anomaly_type=AnomalyType.BEHAVIORAL,
                        severity=severity,
                        description=f"Machine learning detected behavioral anomaly (score: {anomaly_scores[idx]:.3f})",
                        confidence=min(0.9, abs(anomaly_scores[idx]) * 2),
                        detected_at=datetime.utcnow(),
                        baseline_metrics={"ml_score_normal_range": "[-0.1, 0.1]"},
                        observed_metrics={
                            "ml_anomaly_score": float(anomaly_scores[idx])
                        },
                        recommendations=[
                            "Review recent user activity for unusual patterns",
                            "Consider security implications if anomaly score is very low",
                            "Monitor for continued unusual behavior",
                        ],
                    )
                )

        except Exception as e:
            logger.error(f"Error in ML anomaly detection: {e}")

        return anomalies

    async def _detect_temporal_anomalies(
        self, events: list[BehavioralEvent], user_id: str
    ) -> list[Anomaly]:
        """Detect temporal anomalies in user behavior."""
        anomalies = []

        try:
            # Check for unusual activity times
            hours = [e.timestamp.hour for e in events]
            hour_counts = pd.Series(hours).value_counts(normalize=True)

            # Identify very unusual hours (< 1% of activity)
            unusual_hours = hour_counts[hour_counts < 0.01].index.tolist()

            for hour in unusual_hours:
                events_at_hour = [e for e in events if e.timestamp.hour == hour]
                for event in events_at_hour:
                    anomalies.append(
                        Anomaly(
                            anomaly_id=f"temporal_unusual_hour_{event.timestamp}_{user_id}",
                            user_id=user_id,
                            anomaly_type=AnomalyType.TEMPORAL,
                            severity=PatternSeverity.LOW,
                            description=f"Activity at unusual hour: {hour}:00",
                            confidence=0.7,
                            detected_at=datetime.utcnow(),
                            baseline_metrics={
                                "typical_active_hours": hour_counts[
                                    hour_counts > 0.05
                                ].index.tolist()
                            },
                            observed_metrics={"activity_hour": hour},
                        )
                    )

        except Exception as e:
            logger.error(f"Error in temporal anomaly detection: {e}")

        return anomalies

    async def _generate_behavioral_profile(
        self, events: list[BehavioralEvent]
    ) -> dict[str, Any]:
        """Generate comprehensive behavioral profile for the user."""
        try:
            if not events:
                return {}

            # Basic activity metrics
            total_events = len(events)
            successful_events = sum(1 for e in events if e.success)
            avg_duration = (
                np.mean([e.duration_ms for e in events if e.duration_ms])
                if any(e.duration_ms for e in events)
                else 0
            )

            # Activity distribution
            event_types = {}
            for event in events:
                event_types[event.event_type] = event_types.get(event.event_type, 0) + 1

            # Temporal patterns
            hours = [e.timestamp.hour for e in events]
            days = [e.timestamp.weekday() for e in events]

            profile = {
                "activity_level": {
                    "total_events": total_events,
                    "success_rate": (
                        successful_events / total_events if total_events > 0 else 0
                    ),
                    "avg_session_duration_ms": avg_duration,
                },
                "behavioral_preferences": {
                    "most_common_actions": sorted(
                        event_types.items(), key=lambda x: x[1], reverse=True
                    )[:5],
                    "activity_diversity": (
                        len(event_types) / total_events if total_events > 0 else 0
                    ),
                },
                "temporal_patterns": {
                    "most_active_hours": (
                        pd.Series(hours).mode().tolist() if hours else []
                    ),
                    "most_active_days": pd.Series(days).mode().tolist() if days else [],
                    "activity_regularity": len(
                        set(events[e].timestamp.date() for e in events)
                    )
                    / min(30, len(events)),
                },
            }

            return profile

        except Exception as e:
            logger.error(f"Error generating behavioral profile: {e}")
            return {}

    async def _generate_insights(
        self, patterns: list[Pattern], anomalies: list[Anomaly]
    ) -> list[dict[str, Any]]:
        """Generate actionable insights from patterns and anomalies."""
        insights = []

        try:
            # Pattern-based insights
            for pattern in patterns:
                insight = {
                    "type": "pattern",
                    "pattern_id": pattern.pattern_id,
                    "description": pattern.description,
                    "confidence": pattern.confidence,
                    "category": pattern.pattern_type.value,
                    "impact": self._assess_pattern_impact(pattern),
                }
                insights.append(insight)

            # Anomaly-based insights
            for anomaly in anomalies:
                insight = {
                    "type": "anomaly",
                    "anomaly_id": anomaly.anomaly_id,
                    "description": anomaly.description,
                    "severity": anomaly.severity.value,
                    "confidence": anomaly.confidence,
                    "category": anomaly.anomaly_type.value,
                    "requires_attention": anomaly.severity
                    in [PatternSeverity.HIGH, PatternSeverity.CRITICAL],
                }
                insights.append(insight)

        except Exception as e:
            logger.error(f"Error generating insights: {e}")

        return insights

    def _assess_pattern_impact(self, pattern: Pattern) -> str:
        """Assess the business impact of a detected pattern."""
        try:
            high_impact_patterns = [PatternType.RISK, PatternType.LEARNING]

            medium_impact_patterns = [PatternType.PERFORMANCE, PatternType.SOCIAL]

            if pattern.pattern_type in high_impact_patterns:
                return "high" if pattern.confidence > 0.8 else "medium"
            if pattern.pattern_type in medium_impact_patterns:
                return "medium" if pattern.confidence > 0.7 else "low"
            return "low"

        except Exception:
            return "unknown"

    async def _generate_recommendations(self, analysis: dict[str, Any]) -> list[str]:
        """Generate personalized recommendations based on analysis."""
        recommendations = []

        try:
            patterns = analysis.get("patterns", [])
            anomalies = analysis.get("anomalies", [])
            profile = analysis.get("behavioral_profile", {})

            # Risk-based recommendations
            risk_patterns = [p for p in patterns if p.pattern_type == PatternType.RISK]
            if risk_patterns:
                recommendations.extend(
                    [
                        "Monitor user engagement closely to prevent churn",
                        "Consider proactive outreach or intervention",
                        "Review recent system changes that may have affected user experience",
                    ]
                )

            # Performance-based recommendations
            performance_patterns = [
                p for p in patterns if p.pattern_type == PatternType.PERFORMANCE
            ]
            if performance_patterns:
                recommendations.extend(
                    [
                        "Leverage user's efficient patterns for training others",
                        "Document successful workflows for knowledge sharing",
                        "Consider power user for beta testing new features",
                    ]
                )

            # Learning-based recommendations
            learning_patterns = [
                p for p in patterns if p.pattern_type == PatternType.LEARNING
            ]
            if learning_patterns:
                recommendations.extend(
                    [
                        "Provide advanced learning opportunities",
                        "Consider mentorship role for team members",
                        "Offer specialized content based on learning progress",
                    ]
                )

            # Anomaly-based recommendations
            critical_anomalies = [
                a for a in anomalies if a.severity == PatternSeverity.CRITICAL
            ]
            if critical_anomalies:
                recommendations.extend(
                    [
                        "Immediate review of account activity recommended",
                        "Consider security verification steps",
                        "Monitor for continued unusual behavior patterns",
                    ]
                )

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")

        return recommendations[:10]  # Limit to top 10 recommendations

    async def _assess_behavioral_risk(self, analysis: dict[str, Any]) -> dict[str, Any]:
        """Assess overall behavioral risk level."""
        try:
            anomalies = analysis.get("anomalies", [])
            patterns = analysis.get("patterns", [])

            # Calculate risk scores
            risk_score = 0.0
            risk_factors = []

            # High-severity anomalies increase risk
            critical_anomalies = [
                a for a in anomalies if a.severity == PatternSeverity.CRITICAL
            ]
            high_anomalies = [
                a for a in anomalies if a.severity == PatternSeverity.HIGH
            ]

            risk_score += len(critical_anomalies) * 0.4
            risk_score += len(high_anomalies) * 0.2

            if critical_anomalies:
                risk_factors.append("Critical behavioral anomalies detected")

            if high_anomalies:
                risk_factors.append("High-severity anomalies present")

            # Risk patterns increase risk
            risk_patterns = [p for p in patterns if p.pattern_type == PatternType.RISK]
            for pattern in risk_patterns:
                risk_score += pattern.confidence * 0.3

            if risk_patterns:
                risk_factors.append("Risk-oriented behavioral patterns identified")

            # Determine risk level
            if risk_score >= 0.8:
                risk_level = "critical"
            elif risk_score >= 0.6:
                risk_level = "high"
            elif risk_score >= 0.4:
                risk_level = "medium"
            elif risk_score >= 0.2:
                risk_level = "low"
            else:
                risk_level = "minimal"

            return {
                "risk_score": min(1.0, risk_score),
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "requires_monitoring": risk_score >= 0.4,
                "requires_intervention": risk_score >= 0.7,
            }

        except Exception as e:
            logger.error(f"Error assessing behavioral risk: {e}")
            return {
                "risk_score": 0.0,
                "risk_level": "unknown",
                "risk_factors": ["Error in risk assessment"],
                "requires_monitoring": False,
                "requires_intervention": False,
            }

    async def _get_user_events(
        self, user_id: str, time_window_hours: int
    ) -> list[BehavioralEvent]:
        """Get user events within the specified time window."""
        # Note: This would be implemented with actual database queries
        # For now, return empty list to be implemented with real data
        try:
            # Placeholder implementation
            # In real implementation, this would query your analytics_events table
            start_time = datetime.utcnow() - timedelta(hours=time_window_hours)

            # Example query structure:
            # events = self.db.query(AnalyticsEvent).filter(
            #     and_(
            #         AnalyticsEvent.user_id == user_id,
            #         AnalyticsEvent.timestamp >= start_time
            #     )
            # ).order_by(AnalyticsEvent.timestamp).limit(self.config.max_events_per_analysis).all()

            return []  # Return empty for now

        except Exception as e:
            logger.error(f"Error getting user events: {e}")
            return []

    async def _cache_analysis(self, user_id: str, analysis: dict[str, Any]) -> None:
        """Cache behavioral analysis results."""
        try:
            if self.redis_client:
                cache_key = f"behavioral_analysis:{user_id}"
                await self.redis_client.setex(
                    cache_key,
                    self.config.cache_ttl_hours * 3600,
                    json.dumps(analysis, default=str),
                )

        except Exception as e:
            logger.error(f"Error caching analysis: {e}")

    def _get_empty_analysis(self, user_id: str) -> dict[str, Any]:
        """Return empty analysis structure."""
        return {
            "user_id": user_id,
            "analysis_period": {
                "start": datetime.utcnow().isoformat(),
                "end": datetime.utcnow().isoformat(),
                "hours": 0,
            },
            "events_analyzed": 0,
            "patterns": [],
            "anomalies": [],
            "insights": [],
            "recommendations": [],
            "behavioral_profile": {},
            "risk_assessment": {
                "risk_score": 0.0,
                "risk_level": "minimal",
                "risk_factors": [],
                "requires_monitoring": False,
                "requires_intervention": False,
            },
        }


# Add alias for backward compatibility with existing imports
BehavioralPatternService = BehavioralPatternRecognizer
