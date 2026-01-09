"""
Advanced Change Detection Service
Specialized service for detecting various types of changes in behavioral patterns.
Implements state-of-the-art algorithms for real-time and batch change detection.

Key Features:
- Multiple change detection algorithms (CUSUM, EWMA, Bayesian, ML-based)
- Real-time streaming change detection
- Multi-dimensional change detection
- Adaptive thresholding and drift detection
- Early warning system for behavioral changes
- Statistical significance testing
- Change impact assessment and prioritization
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
from typing import Any
import warnings

import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")

# Machine learning libraries
try:
    from sklearn.decomposition import PCA
    from sklearn.ensemble import IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.svm import OneClassSVM

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False

# Time series libraries
try:
    import ruptures as rpt
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller, kpss

    ADVANCED_TS_AVAILABLE = True
except ImportError:
    ADVANCED_TS_AVAILABLE = False

import redis.asyncio as redis
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ChangeDetectionMode(Enum):
    """Modes for change detection."""

    REAL_TIME = "real_time"  # Continuous monitoring
    BATCH = "batch"  # Periodic analysis
    HYBRID = "hybrid"  # Combination of real-time and batch
    RETROSPECTIVE = "retrospective"  # Historical analysis


class ChangeSeverity(Enum):
    """Severity levels for detected changes."""

    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    CRITICAL = "critical"


class DetectionAlgorithm(Enum):
    """Advanced change detection algorithms."""

    ADAPTIVE_CUSUM = "adaptive_cusum"
    EWMA = "ewma"
    BAYESIAN_ONLINE = "bayesian_online"
    PAGE_HINKLEY = "page_hinkley"
    ADWIN = "adwin"
    DDM = "ddm"
    EDDM = "eddm"
    PROXIMITY_STREAM = "proximity_stream"
    ENSEMBLE_STREAM = "ensemble_stream"
    MULTIVARIATE_HOTELLING = "multivariate_hotelling"
    CHANGE_FINDER = "change_finder"


@dataclass
class ChangeAlert:
    """Alert for detected change."""

    alert_id: str
    user_id: str
    metric_name: str
    algorithm: DetectionAlgorithm
    change_type: str
    severity: ChangeSeverity
    detected_at: datetime
    baseline_value: float
    current_value: float
    change_magnitude: float
    confidence: float
    statistical_significance: float
    description: str
    recommended_actions: list[str] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)
    false_positive_probability: float = 0.0


@dataclass
class StreamingDetectionState:
    """State for streaming change detection algorithms."""

    algorithm: DetectionAlgorithm
    parameters: dict[str, Any]
    current_statistics: dict[str, float]
    detection_history: list[datetime] = field(default_factory=list)
    false_positive_count: int = 0
    true_positive_count: int = 0
    last_update: datetime = field(default_factory=datetime.utcnow)


class ChangeDetectionConfig:
    """Configuration for change detection service."""

    # General settings
    default_significance_level: float = 0.05
    min_observations: int = 20
    max_false_positive_rate: float = 0.1
    alert_cooldown_minutes: int = 60

    # Algorithm-specific parameters
    cusum_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "k": 0.5,  # Reference value
            "h": 5.0,  # Decision threshold
            "baseline_window": 30,
        }
    )

    ewma_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "alpha": 0.3,  # Smoothing factor
            "lambda": 3.0,  # Control limit multiplier
            "baseline_window": 30,
        }
    )

    bayesian_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "prior_mean": 0.0,
            "prior_variance": 1.0,
            "likelihood_variance": 0.5,
            "threshold": 0.95,
        }
    )

    page_hinkley_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "delta": 0.005,  # Minimum change magnitude
            "lambda": 50.0,  # Threshold
            "alpha": 0.9999,  # Forgetting factor
        }
    )

    adwin_parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "delta": 0.002,  # Confidence parameter
            "max_buckets": 5,
            "min_window_size": 10,
        }
    )

    # Multi-dimensional settings
    multivariate_threshold: float = 3.0
    pca_components: int = 0.95  # Keep 95% variance
    correlation_threshold: float = 0.8

    # Performance settings
    batch_size: int = 1000
    processing_delay_ms: int = 100
    cache_ttl_hours: int = 24

    # Redis configuration
    redis_url: str = "redis://localhost:6379/9"


class AdvancedChangeDetector:
    """
    Advanced change detection service with multiple algorithms and real-time capabilities.
    """

    def __init__(self, db_session: Session, config: ChangeDetectionConfig | None = None):
        self.db = db_session
        self.config = config or ChangeDetectionConfig()
        self.redis_client: redis.Redis | None = None
        self._init_redis()

        # Initialize algorithm states for streaming detection
        self.streaming_states: dict[str, dict[str, StreamingDetectionState]] = {}

        # Initialize ML models if available
        self.ml_models = {}
        if ML_AVAILABLE:
            self._initialize_ml_models()

        # Check advanced time series library availability
        self.advanced_ts_available = ADVANCED_TS_AVAILABLE
        self.ruptures_available = ADVANCED_TS_AVAILABLE

        logger.info(
            f"Change detector initialized - ML: {ML_AVAILABLE}, Advanced TS: {self.advanced_ts_available}"
        )

    def _init_redis(self) -> None:
        """Initialize Redis connection for caching and state management."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
            )
            logger.info("Change detection Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for change detection: {e}")
            self.redis_client = None

    def _initialize_ml_models(self) -> None:
        """Initialize machine learning models for change detection."""
        try:
            self.ml_models = {
                "isolation_forest": IsolationForest(
                    contamination=0.1, random_state=42, n_estimators=100
                ),
                "one_class_svm": OneClassSVM(nu=0.1, kernel="rbf", gamma="scale"),
                "scaler": StandardScaler(),
                "pca": PCA(n_components=self.config.pca_components),
            }
        except Exception as e:
            logger.error(f"Error initializing ML models: {e}")
            self.ml_models = {}

    async def detect_changes_streaming(
        self,
        user_id: str,
        metric_name: str,
        new_value: float,
        timestamp: datetime | None = None,
        algorithms: list[DetectionAlgorithm] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[ChangeAlert]:
        """
        Real-time change detection for streaming data.

        Args:
            user_id: User ID to monitor
            metric_name: Metric name to monitor
            new_value: New data point value
            timestamp: Timestamp of data point
            algorithms: Algorithms to use for detection
            context: Additional context information

        Returns:
            List of change alerts
        """
        try:
            if timestamp is None:
                timestamp = datetime.utcnow()

            algorithms = algorithms or [
                DetectionAlgorithm.ADAPTIVE_CUSUM,
                DetectionAlgorithm.EWMA,
                DetectionAlgorithm.PAGE_HINKLEY,
            ]

            alerts = []
            user_key = f"{user_id}:{metric_name}"

            # Initialize user state if needed
            if user_key not in self.streaming_states:
                await self._initialize_user_state(user_id, metric_name, algorithms)

            # Run each algorithm
            for algorithm in algorithms:
                try:
                    state = self.streaming_states[user_key].get(algorithm.value)
                    if not state:
                        continue

                    alert = await self._run_streaming_algorithm(
                        algorithm, state, new_value, timestamp, context or {}
                    )

                    if alert:
                        alerts.append(alert)
                        # Update state with detection
                        state.detection_history.append(timestamp)

                except Exception as e:
                    logger.error(f"Error in streaming algorithm {algorithm.value}: {e}")

            # Filter and prioritize alerts
            filtered_alerts = await self._filter_and_prioritize_alerts(alerts)

            # Store alerts
            if filtered_alerts:
                await self._store_change_alerts(filtered_alerts)

            return filtered_alerts

        except Exception as e:
            logger.error(f"Error in streaming change detection for user {user_id}: {e}")
            return []

    async def detect_changes_batch(
        self,
        user_id: str,
        metric_name: str,
        data_points: list[tuple[datetime, float]],
        algorithms: list[DetectionAlgorithm] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[ChangeAlert]:
        """
        Batch change detection for historical data analysis.

        Args:
            user_id: User ID to analyze
            metric_name: Metric name to analyze
            data_points: List of (timestamp, value) tuples
            algorithms: Algorithms to use for detection
            context: Additional context information

        Returns:
            List of change alerts
        """
        try:
            if len(data_points) < self.config.min_observations:
                logger.warning(f"Insufficient data points for batch detection: {len(data_points)}")
                return []

            timestamps, values = zip(*data_points)
            timestamps = list(timestamps)
            values = list(values)

            algorithms = algorithms or [
                DetectionAlgorithm.CHANGE_FINDER,
                DetectionAlgorithm.MULTIVARIATE_HOTELLING,
                DetectionAlgorithm.ENSEMBLE_STREAM,
            ]

            alerts = []

            for algorithm in algorithms:
                try:
                    algorithm_alerts = await self._run_batch_algorithm(
                        algorithm, user_id, metric_name, timestamps, values, context or {}
                    )
                    alerts.extend(algorithm_alerts)

                except Exception as e:
                    logger.error(f"Error in batch algorithm {algorithm.value}: {e}")

            # Consolidate nearby alerts
            consolidated_alerts = await self._consolidate_alerts(alerts)

            # Store alerts
            if consolidated_alerts:
                await self._store_change_alerts(consolidated_alerts)

            return consolidated_alerts

        except Exception as e:
            logger.error(f"Error in batch change detection for user {user_id}: {e}")
            return []

    async def detect_multivariate_changes(
        self,
        user_id: str,
        metrics_data: dict[str, list[tuple[datetime, float]]],
        correlation_threshold: float | None = None,
    ) -> list[ChangeAlert]:
        """
        Detect changes in multivariate behavioral patterns.

        Args:
            user_id: User ID to analyze
            metrics_data: Dictionary of metric_name -> [(timestamp, value)] data
            correlation_threshold: Threshold for correlation-based change detection

        Returns:
            List of change alerts
        """
        try:
            if not metrics_data:
                return []

            # Prepare multivariate data
            aligned_data = await self._align_multivariate_data(metrics_data)
            if not aligned_data:
                return []

            # Perform Hotelling T² test
            hotelling_alerts = await self._hotelling_t2_test(user_id, aligned_data)

            # Perform PCA-based change detection
            pca_alerts = await self._pca_change_detection(user_id, aligned_data)

            # Perform correlation change detection
            correlation_alerts = await self._correlation_change_detection(
                user_id, aligned_data, correlation_threshold
            )

            # Combine and filter alerts
            all_alerts = hotelling_alerts + pca_alerts + correlation_alerts
            filtered_alerts = await self._filter_multivariate_alerts(all_alerts)

            # Store alerts
            if filtered_alerts:
                await self._store_change_alerts(filtered_alerts)

            return filtered_alerts

        except Exception as e:
            logger.error(f"Error in multivariate change detection for user {user_id}: {e}")
            return []

    async def _initialize_user_state(
        self, user_id: str, metric_name: str, algorithms: list[DetectionAlgorithm]
    ) -> None:
        """Initialize streaming detection state for a user-metric combination."""
        user_key = f"{user_id}:{metric_name}"
        self.streaming_states[user_key] = {}

        for algorithm in algorithms:
            state = StreamingDetectionState(
                algorithm=algorithm,
                parameters=self._get_algorithm_parameters(algorithm),
                current_statistics={
                    "count": 0,
                    "mean": 0.0,
                    "variance": 0.0,
                    "min": float("inf"),
                    "max": float("-inf"),
                },
            )

            self.streaming_states[user_key][algorithm.value] = state

    def _get_algorithm_parameters(self, algorithm: DetectionAlgorithm) -> dict[str, Any]:
        """Get parameters for a specific algorithm."""
        param_map = {
            DetectionAlgorithm.ADAPTIVE_CUSUM: self.config.cusum_parameters,
            DetectionAlgorithm.EWMA: self.config.ewma_parameters,
            DetectionAlgorithm.BAYESIAN_ONLINE: self.config.bayesian_parameters,
            DetectionAlgorithm.PAGE_HINKLEY: self.config.page_hinkley_parameters,
            DetectionAlgorithm.ADWIN: self.config.adwin_parameters,
        }
        return param_map.get(algorithm, {})

    async def _run_streaming_algorithm(
        self,
        algorithm: DetectionAlgorithm,
        state: StreamingDetectionState,
        new_value: float,
        timestamp: datetime,
        context: dict[str, Any],
    ) -> ChangeAlert | None:
        """Run a streaming change detection algorithm."""
        try:
            # Update statistics
            state.count = state.current_statistics["count"] + 1
            state.current_statistics["count"] = state.count

            # Update mean and variance incrementally
            old_mean = state.current_statistics["mean"]
            state.current_statistics["mean"] = old_mean + (new_value - old_mean) / state.count

            if state.count > 1:
                old_variance = state.current_statistics["variance"]
                state.current_statistics["variance"] = (
                    old_variance
                    + (
                        (new_value - old_mean) * (new_value - state.current_statistics["mean"])
                        - old_variance
                    )
                    / state.count
                )

            # Update min/max
            state.current_statistics["min"] = min(state.current_statistics["min"], new_value)
            state.current_statistics["max"] = max(state.current_statistics["max"], new_value)

            # Run specific algorithm
            if algorithm == DetectionAlgorithm.ADAPTIVE_CUSUM:
                return await self._adaptive_cusum_stream(state, new_value, timestamp)
            if algorithm == DetectionAlgorithm.EWMA:
                return await self._ewma_stream(state, new_value, timestamp)
            if algorithm == DetectionAlgorithm.PAGE_HINKLEY:
                return await self._page_hinkley_stream(state, new_value, timestamp)
            if algorithm == DetectionAlgorithm.ADWIN:
                return await self._adwin_stream(state, new_value, timestamp)
            logger.warning(f"Streaming algorithm {algorithm.value} not implemented")
            return None

        except Exception as e:
            logger.error(f"Error running streaming algorithm {algorithm.value}: {e}")
            return None

    async def _adaptive_cusum_stream(
        self, state: StreamingDetectionState, new_value: float, timestamp: datetime
    ) -> ChangeAlert | None:
        """Adaptive CUSUM streaming algorithm."""
        try:
            params = state.parameters
            k = params["k"]
            h = params["h"]

            # Initialize CUSUM variables if not present
            if "cusum_pos" not in state.current_statistics:
                state.current_statistics["cusum_pos"] = 0.0
                state.current_statistics["cusum_neg"] = 0.0
                state.current_statistics["baseline_mean"] = new_value
                state.current_statistics["baseline_std"] = 1.0

            baseline_mean = state.current_statistics["baseline_mean"]
            baseline_std = max(
                state.current_statistics["baseline_std"], 0.1
            )  # Avoid division by zero

            # Calculate CUSUM statistics
            deviation = new_value - baseline_mean
            state.current_statistics["cusum_pos"] = max(
                0, state.current_statistics["cusum_pos"] + deviation - k * baseline_std
            )
            state.current_statistics["cusum_neg"] = max(
                0, state.current_statistics["cusum_neg"] - deviation - k * baseline_std
            )

            # Check for change
            if (
                state.current_statistics["cusum_pos"] > h
                or state.current_statistics["cusum_neg"] > h
            ):
                # Change detected
                change_type = (
                    "increase" if state.current_statistics["cusum_pos"] > h else "decrease"
                )
                change_magnitude = (
                    state.current_statistics["cusum_pos"]
                    if state.current_statistics["cusum_pos"] > h
                    else state.current_statistics["cusum_neg"]
                )

                # Calculate confidence based on CUSUM value
                confidence = min(1.0, change_magnitude / h)

                # Update baseline
                state.current_statistics["baseline_mean"] = new_value

                # Reset CUSUM
                state.current_statistics["cusum_pos"] = 0.0
                state.current_statistics["cusum_neg"] = 0.0

                return ChangeAlert(
                    alert_id=f"cusum_{state.algorithm.value}_{timestamp.timestamp()}",
                    user_id="",  # Will be filled by caller
                    metric_name="",  # Will be filled by caller
                    algorithm=DetectionAlgorithm.ADAPTIVE_CUSUM,
                    change_type=change_type,
                    severity=self._calculate_severity(change_magnitude, h),
                    detected_at=timestamp,
                    baseline_value=baseline_mean,
                    current_value=new_value,
                    change_magnitude=change_magnitude,
                    confidence=confidence,
                    statistical_significance=1.0 - confidence,
                    description=f"CUSUM detected {change_type} in metric value",
                    recommended_actions=[f"Investigate {change_type} in {state.algorithm.value}"],
                )

        except Exception as e:
            logger.error(f"Error in adaptive CUSUM stream: {e}")

        return None

    async def _ewma_stream(
        self, state: StreamingDetectionState, new_value: float, timestamp: datetime
    ) -> ChangeAlert | None:
        """EWMA (Exponentially Weighted Moving Average) streaming algorithm."""
        try:
            params = state.parameters
            alpha = params["alpha"]
            lambda_param = params["lambda"]

            # Initialize EWMA variables if not present
            if "ewma" not in state.current_statistics:
                state.current_statistics["ewma"] = new_value
                state.current_statistics["ewma_variance"] = 1.0

            old_ewma = state.current_statistics["ewma"]
            new_ewma = alpha * new_value + (1 - alpha) * old_ewma
            state.current_statistics["ewma"] = new_ewma

            # Update EWMA variance
            ewma_variance = (
                alpha * (new_value - new_ewma) ** 2
                + (1 - alpha) * state.current_statistics["ewma_variance"]
            )
            state.current_statistics["ewma_variance"] = ewma_variance

            # Calculate control limits
            std_dev = np.sqrt(ewma_variance)
            ucl = new_ewma + lambda_param * std_dev
            lcl = new_ewma - lambda_param * std_dev

            # Check for change
            if new_value > ucl or new_value < lcl:
                change_type = "upper" if new_value > ucl else "lower"
                deviation = abs(new_value - new_ewma) / std_dev

                confidence = min(1.0, deviation / lambda_param)

                return ChangeAlert(
                    alert_id=f"ewma_{state.algorithm.value}_{timestamp.timestamp()}",
                    user_id="",
                    metric_name="",
                    algorithm=DetectionAlgorithm.EWMA,
                    change_type=change_type,
                    severity=self._calculate_severity(deviation, lambda_param),
                    detected_at=timestamp,
                    baseline_value=new_ewma,
                    current_value=new_value,
                    change_magnitude=deviation,
                    confidence=confidence,
                    statistical_significance=1.0 - confidence,
                    description=f"EWMA detected {change_type} control limit violation",
                    recommended_actions=[f"Monitor {change_type} trend in metric"],
                )

        except Exception as e:
            logger.error(f"Error in EWMA stream: {e}")

        return None

    async def _page_hinkley_stream(
        self, state: StreamingDetectionState, new_value: float, timestamp: datetime
    ) -> ChangeAlert | None:
        """Page-Hinkley streaming change detection algorithm."""
        try:
            params = state.parameters
            delta = params["delta"]
            lambda_param = params["lambda"]
            alpha = params["alpha"]

            # Initialize Page-Hinkley variables if not present
            if "ph_mean" not in state.current_statistics:
                state.current_statistics["ph_mean"] = new_value
                state.current_statistics["ph_mh"] = 0.0
                state.current_statistics["ph_ml"] = 0.0

            old_mean = state.current_statistics["ph_mean"]
            new_mean = alpha * old_mean + (1 - alpha) * new_value
            state.current_statistics["ph_mean"] = new_mean

            # Update Page-Hinkley statistics
            state.current_statistics["ph_mh"] = max(
                state.current_statistics["ph_mh"] + (new_value - new_mean - delta), 0
            )
            state.current_statistics["ph_ml"] = max(
                state.current_statistics["ph_ml"] - (new_value - new_mean + delta), 0
            )

            # Check for change
            if (
                state.current_statistics["ph_mh"] > lambda_param
                or state.current_statistics["ph_ml"] > lambda_param
            ):
                change_type = (
                    "increase" if state.current_statistics["ph_mh"] > lambda_param else "decrease"
                )
                ph_value = (
                    state.current_statistics["ph_mh"]
                    if state.current_statistics["ph_mh"] > lambda_param
                    else state.current_statistics["ph_ml"]
                )

                confidence = min(1.0, ph_value / lambda_param)

                # Reset statistics after change detection
                state.current_statistics["ph_mh"] = 0.0
                state.current_statistics["ph_ml"] = 0.0

                return ChangeAlert(
                    alert_id=f"page_hinkley_{state.algorithm.value}_{timestamp.timestamp()}",
                    user_id="",
                    metric_name="",
                    algorithm=DetectionAlgorithm.PAGE_HINKLEY,
                    change_type=change_type,
                    severity=self._calculate_severity(ph_value, lambda_param),
                    detected_at=timestamp,
                    baseline_value=old_mean,
                    current_value=new_value,
                    change_magnitude=ph_value,
                    confidence=confidence,
                    statistical_significance=1.0 - confidence,
                    description=f"Page-Hinkley detected {change_type} change",
                    recommended_actions=["Investigate recent behavioral changes"],
                )

        except Exception as e:
            logger.error(f"Error in Page-Hinkley stream: {e}")

        return None

    async def _adwin_stream(
        self, state: StreamingDetectionState, new_value: float, timestamp: datetime
    ) -> ChangeAlert | None:
        """ADWIN (Adaptive Windowing) streaming algorithm."""
        try:
            params = state.parameters
            delta = params["delta"]
            max_buckets = params["max_buckets"]
            min_window_size = params["min_window_size"]

            # Initialize ADWIN window if not present
            if "adwin_window" not in state.current_statistics:
                state.current_statistics["adwin_window"] = deque([new_value], maxlen=1000)
                state.current_statistics["adwin_buckets"] = [deque([new_value])]

            window = state.current_statistics["adwin_window"]
            window.append(new_value)

            # Split window and test for difference
            if len(window) >= min_window_size * 2:
                # Find best split point
                best_split = -1
                best_p_value = 1.0

                for split_point in range(min_window_size, len(window) - min_window_size + 1):
                    window1 = list(window)[:split_point]
                    window2 = list(window)[split_point:]

                    # Perform statistical test
                    try:
                        stat, p_value = stats.ttest_ind(window1, window2)
                        if p_value < best_p_value:
                            best_p_value = p_value
                            best_split = split_point
                    except:
                        continue

                # If significant difference found, update window
                if best_p_value < delta and best_split > 0:
                    # Keep only recent part of window
                    new_window = deque(list(window)[best_split:], maxlen=1000)
                    state.current_statistics["adwin_window"] = new_window

                    # Calculate change metrics
                    old_mean = np.mean(list(window)[:best_split])
                    new_mean = np.mean(list(window)[best_split:])
                    change_magnitude = abs(new_mean - old_mean)

                    confidence = 1.0 - best_p_value

                    return ChangeAlert(
                        alert_id=f"adwin_{state.algorithm.value}_{timestamp.timestamp()}",
                        user_id="",
                        metric_name="",
                        algorithm=DetectionAlgorithm.ADWIN,
                        change_type="distribution_shift",
                        severity=self._calculate_severity(change_magnitude, np.std(list(window))),
                        detected_at=timestamp,
                        baseline_value=old_mean,
                        current_value=new_mean,
                        change_magnitude=change_magnitude,
                        confidence=confidence,
                        statistical_significance=best_p_value,
                        description=f"ADWIN detected distribution change (p={best_p_value:.4f})",
                        recommended_actions=["Investigate change in data distribution"],
                    )

        except Exception as e:
            logger.error(f"Error in ADWIN stream: {e}")

        return None

    async def _run_batch_algorithm(
        self,
        algorithm: DetectionAlgorithm,
        user_id: str,
        metric_name: str,
        timestamps: list[datetime],
        values: list[float],
        context: dict[str, Any],
    ) -> list[ChangeAlert]:
        """Run a batch change detection algorithm."""
        try:
            if algorithm == DetectionAlgorithm.CHANGE_FINDER and self.advanced_ts_available:
                return await self._change_finder_batch(user_id, metric_name, timestamps, values)
            if algorithm == DetectionAlgorithm.MULTIVARIATE_HOTELLING and ML_AVAILABLE:
                return await self._hotelling_t2_batch(user_id, metric_name, timestamps, values)
            if algorithm == DetectionAlgorithm.ENSEMBLE_STREAM and ML_AVAILABLE:
                return await self._ensemble_batch(user_id, metric_name, timestamps, values)
            logger.warning(f"Batch algorithm {algorithm.value} not available")
            return []

        except Exception as e:
            logger.error(f"Error running batch algorithm {algorithm.value}: {e}")
            return []

    async def _change_finder_batch(
        self, user_id: str, metric_name: str, timestamps: list[datetime], values: list[float]
    ) -> list[ChangeAlert]:
        """Change Finder algorithm for batch change detection."""
        try:
            if not self.ruptures_available:
                return []

            signal = np.array(values)

            # Use Pelt algorithm for change point detection
            model = "l2"  # L2 norm (mean shift)
            pen = 10  # Penalty value
            algo = rpt.Pelt(model=model, min_size=5, jump=1).fit(signal)
            result = algo.predict(pen=pen)

            # Extract change points (excluding last point)
            change_indices = result[:-1]

            alerts = []
            for change_idx in change_indices:
                if change_idx < len(timestamps):
                    # Calculate change metrics
                    baseline_values = values[:change_idx]
                    post_change_values = values[change_idx:]

                    if len(baseline_values) >= 3 and len(post_change_values) >= 3:
                        baseline_mean = np.mean(baseline_values)
                        post_change_mean = np.mean(post_change_values)
                        change_magnitude = abs(post_change_mean - baseline_mean)

                        alert = ChangeAlert(
                            alert_id=f"change_finder_{user_id}_{metric_name}_{change_idx}",
                            user_id=user_id,
                            metric_name=metric_name,
                            algorithm=DetectionAlgorithm.CHANGE_FINDER,
                            change_type="level_shift",
                            severity=self._calculate_severity(change_magnitude, np.std(values)),
                            detected_at=timestamps[change_idx],
                            baseline_value=baseline_mean,
                            current_value=post_change_mean,
                            change_magnitude=change_magnitude,
                            confidence=0.8,  # Fixed confidence for Pelt
                            statistical_significance=0.05,
                            description="Change Finder detected level shift",
                            recommended_actions=["Investigate behavioral pattern change"],
                        )
                        alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Error in Change Finder batch: {e}")
            return []

    async def _ensemble_batch(
        self, user_id: str, metric_name: str, timestamps: list[datetime], values: list[float]
    ) -> list[ChangeAlert]:
        """Ensemble method combining multiple change detection algorithms."""
        try:
            # Combine results from multiple algorithms
            all_change_indices = []

            # Try different algorithms
            algorithms = [
                ("cusum", self._cusum_batch_indices),
                ("ewma", self._ewma_batch_indices),
                ("statistical", self._statistical_batch_indices),
            ]

            for alg_name, alg_func in algorithms:
                try:
                    indices = alg_func(values)
                    all_change_indices.extend([(idx, alg_name) for idx in indices])
                except Exception as e:
                    logger.debug(f"Error in ensemble algorithm {alg_name}: {e}")

            # Find consensus change points
            consensus_points = self._find_consensus_changes(all_change_indices, len(values))

            alerts = []
            for change_idx, consensus_info in consensus_points:
                if change_idx < len(timestamps):
                    baseline_values = values[:change_idx]
                    post_change_values = values[change_idx:]

                    if len(baseline_values) >= 3 and len(post_change_values) >= 3:
                        baseline_mean = np.mean(baseline_values)
                        post_change_mean = np.mean(post_change_values)
                        change_magnitude = abs(post_change_mean - baseline_mean)

                        # Confidence based on consensus level
                        confidence = consensus_info["consensus_level"] / len(algorithms)

                        alert = ChangeAlert(
                            alert_id=f"ensemble_{user_id}_{metric_name}_{change_idx}",
                            user_id=user_id,
                            metric_name=metric_name,
                            algorithm=DetectionAlgorithm.ENSEMBLE_STREAM,
                            change_type="consensus_change",
                            severity=self._calculate_severity(change_magnitude, np.std(values)),
                            detected_at=timestamps[change_idx],
                            baseline_value=baseline_mean,
                            current_value=post_change_mean,
                            change_magnitude=change_magnitude,
                            confidence=confidence,
                            statistical_significance=1.0 - confidence,
                            description=f"Ensemble detected change (consensus: {consensus_info['algorithms']})",
                            recommended_actions=[
                                "Multi-algorithm consensus indicates significant change"
                            ],
                            context={"consensus_info": consensus_info},
                        )
                        alerts.append(alert)

            return alerts

        except Exception as e:
            logger.error(f"Error in ensemble batch: {e}")
            return []

    def _cusum_batch_indices(self, values: list[float]) -> list[int]:
        """CUSUM batch implementation returning change indices."""
        try:
            if len(values) < 20:
                return []

            baseline_size = len(values) // 3
            baseline_mean = np.mean(values[:baseline_size])
            baseline_std = np.std(values[:baseline_size])

            if baseline_std == 0:
                return []

            cusum_values = []
            k = baseline_std / 2
            h = 5 * baseline_std

            current_cusum = 0
            change_indices = []

            for i, value in enumerate(values):
                deviation = value - baseline_mean
                current_cusum = max(0, current_cusum + deviation - k)

                if current_cusum > h:
                    change_indices.append(i)
                    current_cusum = 0

            return change_indices

        except Exception:
            return []

    def _ewma_batch_indices(self, values: list[float]) -> list[int]:
        """EWMA batch implementation returning change indices."""
        try:
            if len(values) < 20:
                return []

            alpha = 0.3
            lambda_param = 3.0
            ewma_values = []
            current_ewma = values[0]

            for value in values:
                current_ewma = alpha * value + (1 - alpha) * current_ewma
                ewma_values.append(current_ewma)

            # Calculate control limits
            std_dev = np.std(ewma_values)
            change_indices = []

            for i, value in enumerate(values):
                ucl = ewma_values[i] + lambda_param * std_dev
                lcl = ewma_values[i] - lambda_param * std_dev

                if value > ucl or value < lcl:
                    change_indices.append(i)

            return change_indices

        except Exception:
            return []

    def _statistical_batch_indices(self, values: list[float]) -> list[int]:
        """Statistical batch implementation using sliding window t-tests."""
        try:
            if len(values) < 40:
                return []

            window_size = 20
            change_indices = []

            for i in range(window_size, len(values) - window_size):
                before_window = values[i - window_size : i]
                after_window = values[i : i + window_size]

                t_stat, p_value = stats.ttest_ind(before_window, after_window)

                if p_value < 0.05:  # Significance threshold
                    change_indices.append(i)

            return change_indices

        except Exception:
            return []

    def _find_consensus_changes(
        self, all_changes: list[tuple[int, str]], data_length: int
    ) -> list[tuple[int, dict[str, Any]]]:
        """Find consensus change points from multiple algorithms."""
        try:
            if not all_changes:
                return []

            # Group changes by proximity (within 5 indices)
            tolerance = 5
            consensus_groups = []

            for change_idx, algorithm in all_changes:
                # Find existing group
                assigned = False
                for group in consensus_groups:
                    if abs(change_idx - group["center"]) <= tolerance:
                        group["indices"].append(change_idx)
                        group["algorithms"].append(algorithm)
                        # Update center to be mean of indices
                        group["center"] = np.mean(group["indices"])
                        assigned = True
                        break

                if not assigned:
                    consensus_groups.append(
                        {"center": change_idx, "indices": [change_idx], "algorithms": [algorithm]}
                    )

            # Filter groups with consensus (at least 2 algorithms)
            consensus_points = []
            for group in consensus_groups:
                if len(group["algorithms"]) >= 2:
                    consensus_points.append(
                        (
                            int(round(group["center"])),
                            {
                                "consensus_level": len(group["algorithms"]),
                                "algorithms": group["algorithms"],
                                "indices": group["indices"],
                            },
                        )
                    )

            return consensus_points

        except Exception:
            return []

    def _calculate_severity(self, change_magnitude: float, threshold: float) -> ChangeSeverity:
        """Calculate severity level based on change magnitude and threshold."""
        try:
            ratio = change_magnitude / threshold if threshold > 0 else 0

            if ratio >= 3.0:
                return ChangeSeverity.CRITICAL
            if ratio >= 2.0:
                return ChangeSeverity.SIGNIFICANT
            if ratio >= 1.0:
                return ChangeSeverity.MODERATE
            return ChangeSeverity.MINOR

        except Exception:
            return ChangeSeverity.MODERATE

    # TODO(human): Implement remaining methods for multivariate analysis, alert management, and database operations
    async def _align_multivariate_data(
        self, metrics_data: dict[str, list[tuple[datetime, float]]]
    ) -> pd.DataFrame | None:
        """Align multivariate time series data by timestamps."""
        return None

    async def _hotelling_t2_test(
        self, user_id: str, aligned_data: pd.DataFrame
    ) -> list[ChangeAlert]:
        """Perform Hotelling T² test for multivariate change detection."""
        return []

    async def _pca_change_detection(
        self, user_id: str, aligned_data: pd.DataFrame
    ) -> list[ChangeAlert]:
        """Perform PCA-based change detection."""
        return []

    async def _correlation_change_detection(
        self, user_id: str, aligned_data: pd.DataFrame, correlation_threshold: float | None
    ) -> list[ChangeAlert]:
        """Detect changes in correlation patterns."""
        return []

    async def _filter_and_prioritize_alerts(self, alerts: list[ChangeAlert]) -> list[ChangeAlert]:
        """Filter and prioritize change alerts."""
        return alerts

    async def _filter_multivariate_alerts(self, alerts: list[ChangeAlert]) -> list[ChangeAlert]:
        """Filter multivariate change alerts."""
        return alerts

    async def _consolidate_alerts(self, alerts: list[ChangeAlert]) -> list[ChangeAlert]:
        """Consolidate nearby change alerts."""
        return alerts

    async def _store_change_alerts(self, alerts: list[ChangeAlert]) -> None:
        """Store change alerts in database."""
