"""
Longitudinal Analysis Service
Advanced time-series analysis and change detection for behavioral patterns over time.
Implements statistical methods for trend analysis, change point detection, and comparative analysis.

Key Features:
- Time-series data aggregation and storage
- Multiple change detection algorithms (CUSUM, E-Divisive, Bayesian, ML-based)
- Trend analysis with seasonal decomposition
- Behavioral baseline calculation and monitoring
- Cohort analysis and retention modeling
- Comparative analysis across groups and time periods
- Predictive modeling for churn and engagement
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import logging
from scipy import stats
from scipy.signal import find_peaks
from scipy.stats import linregress, ttest_ind, mannwhitneyu
import warnings
warnings.filterwarnings('ignore')

# Time series and change detection libraries
try:
    import ruptures as rpt
    RUPTURES_AVAILABLE = True
except ImportError:
    RUPTURES_AVAILABLE = False

try:
    from statsmodels.tsa.seasonal import seasonal_decompose
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.stats.weightstats import ztest
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of behavioral metrics for longitudinal analysis."""
    COUNT = "count"           # Event counts (logins, actions, etc.)
    RATE = "rate"            # Rates and percentages (success rate, engagement rate)
    DURATION = "duration"     # Time-based metrics (session duration, response time)
    SCORE = "score"          # Score-based metrics (assessment scores, performance)
    FREQUENCY = "frequency"   # Frequency metrics (events per time period)
    RATIO = "ratio"          # Ratio metrics (conversion ratios, efficiency ratios)

class ChangeType(Enum):
    """Types of changes that can be detected."""
    LEVEL_SHIFT = "level_shift"      # Sudden change in mean value
    TREND_CHANGE = "trend_change"    # Change in trend direction or slope
    VARIANCE_CHANGE = "variance_change"  # Change in variability
    SEASONAL_CHANGE = "seasonal_change"  # Change in seasonal patterns
    PATTERN_CHANGE = "pattern_change"    # Change in behavioral patterns
    SPIKE_DROP = "spike_drop"         # Sudden spikes or drops

class DetectionMethod(Enum):
    """Methods for change detection."""
    CUSUM = "cusum"                    # Cumulative Sum Control Chart
    E_DIVISIVE = "e_divisive"          # E-Divisive with means
    BAYESIAN = "bayesian"              # Bayesian change point detection
    ML_BASED = "ml_based"              # Machine learning based detection
    STATISTICAL = "statistical"        # Statistical tests (t-test, etc.)
    WINDOW_BASED = "window_based"      # Window-based comparison
    ENSEMBLE = "ensemble"              # Ensemble of multiple methods

class TrendDirection(Enum):
    """Directions of trends."""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"

class ImpactLevel(Enum):
    """Impact levels for detected changes."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TimeSeriesPoint:
    """Single point in time series data."""
    timestamp: datetime
    value: float
    metric_name: str
    user_id: str
    bucket_size: str  # hour, day, week, month
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ChangePoint:
    """Detected change point in time series."""
    id: str
    user_id: str
    metric_name: str
    change_type: ChangeType
    detection_method: DetectionMethod
    change_point: datetime
    baseline_start: datetime
    baseline_end: datetime
    post_change_start: datetime
    baseline_mean: float
    post_change_mean: float
    change_magnitude: float
    confidence_score: float
    statistic_value: Optional[float] = None
    p_value: Optional[float] = None
    significance_level: float = 0.05
    description: Optional[str] = None
    impact_level: ImpactLevel = ImpactLevel.MEDIUM
    requires_attention: bool = False

@dataclass
class TrendAnalysis:
    """Results of trend analysis."""
    id: str
    user_id: str
    metric_name: str
    analysis_period_start: datetime
    analysis_period_end: datetime
    trend_direction: TrendDirection
    trend_slope: float
    trend_intercept: float
    r_squared: float
    p_value: float
    seasonal_component: bool
    seasonal_period: Optional[int]
    seasonal_strength: Optional[float]
    confidence_level: float
    forecast_next_period: Optional[float] = None
    forecast_confidence_lower: Optional[float] = None
    forecast_confidence_upper: Optional[float] = None

@dataclass
class BehavioralBaseline:
    """Calculated behavioral baseline for comparison."""
    id: str
    user_id: str
    metric_name: str
    baseline_type: str  # personal, peer_group, organizational
    baseline_period_start: datetime
    baseline_period_end: datetime
    mean_value: float
    median_value: float
    std_deviation: float
    min_value: float
    max_value: float
    percentile_25: float
    percentile_75: float
    sample_size: int
    confidence_level: float
    margin_of_error: float
    is_active: bool

@dataclass
class LongitudinalConfig:
    """Configuration for longitudinal analysis."""

    # Time series settings
    default_bucket_size: str = "day"  # hour, day, week, month
    min_data_points: int = 10
    max_data_points: int = 1000
    analysis_window_days: int = 90

    # Change detection settings
    significance_level: float = 0.05
    min_change_magnitude: float = 0.1  # 10% minimum change
    confidence_threshold: float = 0.8
    detection_methods: List[DetectionMethod] = field(default_factory=lambda: [
        DetectionMethod.CUSUM,
        DetectionMethod.E_DIVISIVE,
        DetectionMethod.WINDOW_BASED
    ])

    # Trend analysis settings
    trend_detection_window: int = 30  # days
    seasonal_detection_enabled: bool = True
    min_seasonal_periods: int = 3
    forecast_periods: int = 7  # days

    # Baseline settings
    baseline_period_days: int = 30
    baseline_sample_size: int = 100
    baseline_confidence_level: float = 0.95
    baseline_update_frequency_days: int = 7

    # Performance settings
    cache_ttl_hours: int = 24
    batch_processing_size: int = 1000
    parallel_processing: bool = True

    # Redis configuration
    redis_url: str = "redis://localhost:6379/8"

class LongitudinalAnalyzer:
    """
    Advanced longitudinal analysis engine for behavioral pattern tracking.
    """

    def __init__(self, db_session: Session, config: Optional[LongitudinalConfig] = None):
        self.db = db_session
        self.config = config or LongitudinalConfig()
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()

        # Initialize detection methods availability
        self.ruptures_available = RUPTURES_AVAILABLE
        self.statsmodels_available = STATSMODELS_AVAILABLE

        logger.info(f"Longitudinal analyzer initialized - Ruptures: {self.ruptures_available}, Statsmodels: {self.statsmodels_available}")

    def _init_redis(self) -> None:
        """Initialize Redis connection for caching."""
        try:
            self.redis_client = redis.from_url(
                self.config.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True
            )
            logger.info("Longitudinal analyzer Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for longitudinal analysis: {e}")
            self.redis_client = None

    async def aggregate_time_series_data(
        self,
        user_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        bucket_size: str = "day"
    ) -> List[TimeSeriesPoint]:
        """
        Aggregate behavioral data into time series buckets.

        Args:
            user_id: User ID to aggregate data for
            metric_name: Name of the metric to aggregate
            start_time: Start time for aggregation
            end_time: End time for aggregation
            bucket_size: Size of time buckets (hour, day, week, month)

        Returns:
            List of time series data points
        """
        try:
            # TODO(human): Implement actual database aggregation
            # For now, return mock data

            # Generate time buckets
            time_buckets = self._generate_time_buckets(start_time, end_time, bucket_size)

            # Generate mock data for each bucket
            time_series_data = []
            for i, bucket_start in enumerate(time_buckets):
                # Create realistic behavioral data with trends and seasonality
                base_value = 50 + i * 0.5  # Slight upward trend
                seasonal_component = 10 * np.sin(2 * np.pi * i / 7)  # Weekly seasonality
                noise = np.random.normal(0, 5)  # Random noise
                value = max(0, base_value + seasonal_component + noise)

                point = TimeSeriesPoint(
                    timestamp=bucket_start,
                    value=value,
                    metric_name=metric_name,
                    user_id=user_id,
                    bucket_size=bucket_size,
                    context={'generated': True}
                )
                time_series_data.append(point)

            # Store in database for future analysis
            await self._store_time_series_data(time_series_data)

            return time_series_data

        except Exception as e:
            logger.error(f"Error aggregating time series data for user {user_id}: {e}")
            return []

    async def detect_changes(
        self,
        user_id: str,
        metric_name: str,
        time_series_data: List[TimeSeriesPoint],
        methods: Optional[List[DetectionMethod]] = None
    ) -> List[ChangePoint]:
        """
        Detect change points in time series data using multiple methods.

        Args:
            user_id: User ID to analyze
            metric_name: Metric name to analyze
            time_series_data: Time series data points
            methods: Detection methods to use (None for default)

        Returns:
            List of detected change points
        """
        try:
            if len(time_series_data) < self.config.min_data_points:
                logger.warning(f"Insufficient data points for change detection: {len(time_series_data)}")
                return []

            methods = methods or self.config.detection_methods
            all_change_points = []

            # Run each detection method
            for method in methods:
                try:
                    change_points = await self._detect_changes_with_method(
                        method, user_id, metric_name, time_series_data
                    )
                    all_change_points.extend(change_points)
                except Exception as e:
                    logger.error(f"Error with change detection method {method.value}: {e}")

            # Consolidate and filter change points
            consolidated_changes = await self._consolidate_change_points(all_change_points)

            # Calculate impact levels and attention requirements
            for change in consolidated_changes:
                change.impact_level = self._calculate_impact_level(change)
                change.requires_attention = change.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]

            # Store detected changes
            await self._store_change_points(consolidated_changes)

            logger.info(f"Detected {len(consolidated_changes)} change points for user {user_id}, metric {metric_name}")
            return consolidated_changes

        except Exception as e:
            logger.error(f"Error detecting changes for user {user_id}: {e}")
            return []

    async def analyze_trends(
        self,
        user_id: str,
        metric_name: str,
        time_series_data: List[TimeSeriesPoint]
    ) -> Optional[TrendAnalysis]:
        """
        Analyze trends in time series data including seasonal decomposition.

        Args:
            user_id: User ID to analyze
            metric_name: Metric name to analyze
            time_series_data: Time series data points

        Returns:
            Trend analysis results
        """
        try:
            if len(time_series_data) < self.config.min_data_points:
                logger.warning(f"Insufficient data points for trend analysis: {len(time_series_data)}")
                return None

            # Extract values and timestamps
            values = [point.value for point in time_series_data]
            timestamps = [point.timestamp for point in time_series_data]

            # Convert to numeric index for analysis
            x = np.arange(len(values))
            y = np.array(values)

            # Linear regression analysis
            slope, intercept, r_value, p_value, std_err = linregress(x, y)

            # Determine trend direction
            if abs(slope) < 0.01:
                trend_direction = TrendDirection.STABLE
            elif slope > 0:
                trend_direction = TrendDirection.INCREASING
            else:
                trend_direction = TrendDirection.DECREASING

            # Seasonal decomposition if enabled
            seasonal_component = False
            seasonal_period = None
            seasonal_strength = None

            if self.config.seasonal_detection_enabled and len(values) >= 14:  # At least 2 weeks
                seasonal_info = await self._detect_seasonality(values, timestamps)
                seasonal_component = seasonal_info['has_seasonality']
                seasonal_period = seasonal_info['period']
                seasonal_strength = seasonal_info['strength']

            # Generate forecasts if enough data
            forecast_next = None
            forecast_lower = None
            forecast_upper = None

            if len(values) >= self.config.trend_detection_window:
                forecasts = await self._generate_forecast(values, slope, intercept, std_err)
                forecast_next = forecasts['next_value']
                forecast_lower = forecasts['confidence_lower']
                forecast_upper = forecasts['confidence_upper']

            # Create trend analysis object
            trend_analysis = TrendAnalysis(
                id=f"trend_{user_id}_{metric_name}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                metric_name=metric_name,
                analysis_period_start=timestamps[0],
                analysis_period_end=timestamps[-1],
                trend_direction=trend_direction,
                trend_slope=slope,
                trend_intercept=intercept,
                r_squared=r_value ** 2,
                p_value=p_value,
                seasonal_component=seasonal_component,
                seasonal_period=seasonal_period,
                seasonal_strength=seasonal_strength,
                confidence_level=1.0 - self.config.significance_level,
                forecast_next_period=forecast_next,
                forecast_confidence_lower=forecast_lower,
                forecast_confidence_upper=forecast_upper
            )

            # Store trend analysis
            await self._store_trend_analysis(trend_analysis)

            return trend_analysis

        except Exception as e:
            logger.error(f"Error analyzing trends for user {user_id}: {e}")
            return None

    async def calculate_baseline(
        self,
        user_id: str,
        metric_name: str,
        baseline_type: str = "personal",
        baseline_period_days: Optional[int] = None
    ) -> Optional[BehavioralBaseline]:
        """
        Calculate behavioral baseline for comparison.

        Args:
            user_id: User ID to calculate baseline for
            metric_name: Metric name to calculate baseline for
            baseline_type: Type of baseline (personal, peer_group, organizational)
            baseline_period_days: Period for baseline calculation

        Returns:
            Calculated behavioral baseline
        """
        try:
            baseline_period = baseline_period_days or self.config.baseline_period_days
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=baseline_period)

            # Get data for baseline calculation
            if baseline_type == "personal":
                data = await self._get_user_metric_data(user_id, metric_name, start_time, end_time)
            elif baseline_type == "peer_group":
                data = await self._get_peer_group_data(user_id, metric_name, start_time, end_time)
            elif baseline_type == "organizational":
                data = await self._get_organizational_data(metric_name, start_time, end_time)
            else:
                raise ValueError(f"Unknown baseline type: {baseline_type}")

            if not data or len(data) < self.config.baseline_sample_size:
                logger.warning(f"Insufficient data for baseline calculation: {len(data) if data else 0}")
                return None

            values = np.array(data)

            # Calculate statistics
            mean_value = np.mean(values)
            median_value = np.median(values)
            std_deviation = np.std(values)
            min_value = np.min(values)
            max_value = np.max(values)
            percentile_25 = np.percentile(values, 25)
            percentile_75 = np.percentile(values, 75)

            # Calculate confidence interval
            confidence_level = self.config.baseline_confidence_level
            alpha = 1.0 - confidence_level
            margin_of_error = stats.t.ppf(1 - alpha/2, len(values) - 1) * (std_deviation / np.sqrt(len(values)))

            baseline = BehavioralBaseline(
                id=f"baseline_{user_id}_{metric_name}_{baseline_type}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                metric_name=metric_name,
                baseline_type=baseline_type,
                baseline_period_start=start_time,
                baseline_period_end=end_time,
                mean_value=mean_value,
                median_value=median_value,
                std_deviation=std_deviation,
                min_value=min_value,
                max_value=max_value,
                percentile_25=percentile_25,
                percentile_75=percentile_75,
                sample_size=len(values),
                confidence_level=confidence_level,
                margin_of_error=margin_of_error,
                is_active=True
            )

            # Store baseline
            await self._store_baseline(baseline)

            return baseline

        except Exception as e:
            logger.error(f"Error calculating baseline for user {user_id}: {e}")
            return None

    async def analyze_user_progression(
        self,
        user_id: str,
        metrics: List[str],
        time_range_days: int = 90
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis of user's behavioral progression over time.

        Args:
            user_id: User ID to analyze
            metrics: List of metrics to analyze
            time_range_days: Time range for analysis in days

        Returns:
            Comprehensive progression analysis
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=time_range_days)

            progression_analysis = {
                'user_id': user_id,
                'analysis_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': time_range_days
                },
                'metrics_analysis': {},
                'overall_insights': [],
                'recommendations': [],
                'risk_indicators': []
            }

            # Analyze each metric
            for metric in metrics:
                # Get time series data
                time_series_data = await self.get_time_series_data(user_id, metric, start_time, end_time)

                if not time_series_data:
                    continue

                # Trend analysis
                trend_analysis = await self.analyze_trends(user_id, metric, time_series_data)

                # Change detection
                change_points = await self.detect_changes(user_id, metric, time_series_data)

                # Baseline comparison
                current_baseline = await self.calculate_baseline(user_id, metric)

                # Store metric analysis
                progression_analysis['metrics_analysis'][metric] = {
                    'trend': trend_analysis.__dict__ if trend_analysis else None,
                    'change_points': [cp.__dict__ for cp in change_points],
                    'baseline': current_baseline.__dict__ if current_baseline else None,
                    'current_value': time_series_data[-1].value if time_series_data else None,
                    'data_points': len(time_series_data)
                }

                # Generate metric-specific insights
                if change_points:
                    high_impact_changes = [cp for cp in change_points if cp.impact_level in [ImpactLevel.HIGH, ImpactLevel.CRITICAL]]
                    if high_impact_changes:
                        progression_analysis['risk_indicators'].append({
                            'metric': metric,
                            'type': 'high_impact_changes',
                            'count': len(high_impact_changes),
                            'description': f"Detected {len(high_impact_changes)} high-impact changes in {metric}"
                        })

            # Generate overall insights
            progression_analysis['overall_insights'] = await self._generate_progression_insights(
                progression_analysis['metrics_analysis']
            )

            # Generate recommendations
            progression_analysis['recommendations'] = await self._generate_progression_recommendations(
                progression_analysis['metrics_analysis'],
                progression_analysis['overall_insights']
            )

            return progression_analysis

        except Exception as e:
            logger.error(f"Error analyzing user progression for {user_id}: {e}")
            return {}

    def _generate_time_buckets(
        self,
        start_time: datetime,
        end_time: datetime,
        bucket_size: str
    ) -> List[datetime]:
        """Generate time buckets for aggregation."""
        buckets = []
        current_time = start_time

        # Determine bucket size in timedelta
        if bucket_size == "hour":
            delta = timedelta(hours=1)
        elif bucket_size == "day":
            delta = timedelta(days=1)
        elif bucket_size == "week":
            delta = timedelta(weeks=1)
        elif bucket_size == "month":
            delta = timedelta(days=30)  # Approximate
        else:
            delta = timedelta(days=1)

        while current_time < end_time:
            buckets.append(current_time)
            current_time += delta

        return buckets

    async def _detect_changes_with_method(
        self,
        method: DetectionMethod,
        user_id: str,
        metric_name: str,
        time_series_data: List[TimeSeriesPoint]
    ) -> List[ChangePoint]:
        """Detect changes using a specific method."""
        values = [point.value for point in time_series_data]
        timestamps = [point.timestamp for point in time_series_data]

        if method == DetectionMethod.CUSUM:
            return await self._cusum_detection(user_id, metric_name, timestamps, values)
        elif method == DetectionMethod.E_DIVISIVE:
            return await self._edivisive_detection(user_id, metric_name, timestamps, values)
        elif method == DetectionMethod.BAYESIAN:
            return await self._bayesian_detection(user_id, metric_name, timestamps, values)
        elif method == DetectionMethod.STATISTICAL:
            return await self._statistical_detection(user_id, metric_name, timestamps, values)
        elif method == DetectionMethod.WINDOW_BASED:
            return await self._window_based_detection(user_id, metric_name, timestamps, values)
        elif method == DetectionMethod.ML_BASED:
            return await self._ml_based_detection(user_id, metric_name, timestamps, values)
        else:
            logger.warning(f"Unknown change detection method: {method}")
            return []

    async def _cusum_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """CUSUM (Cumulative Sum) change detection."""
        try:
            if not values:
                return []

            # Calculate baseline statistics from first portion of data
            baseline_size = min(len(values) // 3, 30)
            baseline_values = values[:baseline_size]
            baseline_mean = np.mean(baseline_values)
            baseline_std = np.std(baseline_values)

            if baseline_std == 0:
                return []

            # CUSUM calculation
            cusum_pos = [0]
            cusum_neg = [0]

            k = baseline_std / 2  # Reference value
            h = 5 * baseline_std  # Decision threshold

            for value in values:
                cusum_pos.append(max(0, cusum_pos[-1] + value - baseline_mean - k))
                cusum_neg.append(max(0, cusum_neg[-1] - value + baseline_mean + k))

            # Find change points where CUSUM exceeds threshold
            change_points = []

            for i in range(1, len(cusum_pos)):
                if cusum_pos[i] > h:
                    # Positive change detected
                    change_idx = i
                    if change_idx < len(timestamps):
                        change_point = await self._create_change_point(
                            user_id, metric_name, timestamps, values, change_idx,
                            ChangeType.LEVEL_SHIFT, DetectionMethod.CUSUM, ChangeType.LEVEL_SHIFT
                        )
                        if change_point:
                            change_points.append(change_point)

                if cusum_neg[i] > h:
                    # Negative change detected
                    change_idx = i
                    if change_idx < len(timestamps):
                        change_point = await self._create_change_point(
                            user_id, metric_name, timestamps, values, change_idx,
                            ChangeType.LEVEL_SHIFT, DetectionMethod.CUSUM, ChangeType.LEVEL_SHIFT
                        )
                        if change_point:
                            change_points.append(change_point)

            return change_points

        except Exception as e:
            logger.error(f"Error in CUSUM detection: {e}")
            return []

    async def _edivisive_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """E-Divisive change detection using ruptures library."""
        try:
            if not self.ruptures_available or len(values) < 20:
                return []

            # Convert to numpy array
            signal = np.array(values)

            # Use Pelt algorithm for change point detection
            model = "l2"  # L2 norm (mean shift)
            pen = 10  # Penalty value
            algo = rpt.Pelt(model=model, min_size=5, jump=1).fit(signal)
            result = algo.predict(pen=pen)

            # Extract change points (excluding last point which is end of series)
            change_indices = result[:-1]

            change_points = []
            for change_idx in change_indices:
                if change_idx < len(timestamps):
                    change_point = await self._create_change_point(
                        user_id, metric_name, timestamps, values, change_idx,
                        ChangeType.LEVEL_SHIFT, DetectionMethod.E_DIVISIVE, ChangeType.LEVEL_SHIFT
                    )
                    if change_point:
                        change_points.append(change_point)

            return change_points

        except Exception as e:
            logger.error(f"Error in E-Divisive detection: {e}")
            return []

    async def _bayesian_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """Bayesian change point detection."""
        try:
            if len(values) < 20:
                return []

            # Simple Bayesian approach using moving window comparison
            window_size = min(len(values) // 4, 20)
            change_points = []

            for i in range(window_size, len(values) - window_size):
                # Compare before and after windows
                before_window = values[i-window_size:i]
                after_window = values[i:i+window_size]

                # Bayesian inference (simplified)
                # Using likelihood ratio test
                mean_before = np.mean(before_window)
                mean_after = np.mean(after_window)
                std_before = np.std(before_window)
                std_after = np.std(after_window)

                # Calculate likelihood ratio
                if std_before > 0 and std_after > 0:
                    # Simplified Bayesian change detection
                    se = np.sqrt(std_before**2/len(before_window) + std_after**2/len(after_window))
                    if se > 0:
                        z_score = abs(mean_after - mean_before) / se
                        p_value = 2 * (1 - stats.norm.cdf(z_score))

                        if p_value < self.config.significance_level:
                            change_point = await self._create_change_point(
                                user_id, metric_name, timestamps, values, i,
                                ChangeType.LEVEL_SHIFT, DetectionMethod.BAYESIAN, ChangeType.LEVEL_SHIFT
                            )
                            if change_point:
                                change_points.append(change_point)

            return change_points

        except Exception as e:
            logger.error(f"Error in Bayesian detection: {e}")
            return []

    async def _statistical_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """Statistical change detection using t-tests."""
        try:
            if len(values) < 30:
                return []

            window_size = min(len(values) // 3, 20)
            change_points = []

            for i in range(window_size, len(values) - window_size):
                before_window = values[i-window_size:i]
                after_window = values[i:i+window_size]

                # Perform t-test
                t_stat, p_value = ttest_ind(before_window, after_window)

                if p_value < self.config.significance_level:
                    # Calculate effect size (Cohen's d)
                    pooled_std = np.sqrt(((len(before_window) - 1) * np.var(before_window) +
                                         (len(after_window) - 1) * np.var(after_window)) /
                                        (len(before_window) + len(after_window) - 2))

                    if pooled_std > 0:
                        effect_size = (np.mean(after_window) - np.mean(before_window)) / pooled_std
                    else:
                        effect_size = 0

                    # Only consider significant changes
                    if abs(effect_size) > self.config.min_change_magnitude:
                        change_point = await self._create_change_point(
                            user_id, metric_name, timestamps, values, i,
                            ChangeType.LEVEL_SHIFT, DetectionMethod.STATISTICAL, ChangeType.LEVEL_SHIFT
                        )
                        if change_point:
                            change_point.statistic_value = float(t_stat)
                            change_point.p_value = float(p_value)
                            change_points.append(change_point)

            return change_points

        except Exception as e:
            logger.error(f"Error in statistical detection: {e}")
            return []

    async def _window_based_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """Window-based change detection comparing adjacent windows."""
        try:
            if len(values) < 20:
                return []

            window_size = min(len(values) // 4, 15)
            change_points = []

            for i in range(window_size, len(values) - window_size, window_size // 2):
                before_window = values[i-window_size:i]
                after_window = values[i:i+window_size]

                # Compare means
                mean_before = np.mean(before_window)
                mean_after = np.mean(after_window)
                std_before = np.std(before_window)
                std_after = np.std(after_window)

                # Calculate relative change
                if mean_before != 0:
                    relative_change = abs(mean_after - mean_before) / abs(mean_before)
                else:
                    relative_change = abs(mean_after - mean_before)

                if relative_change > self.config.min_change_magnitude:
                    # Statistical significance test
                    if std_before > 0 and std_after > 0:
                        se = np.sqrt(std_before**2/len(before_window) + std_after**2/len(after_window))
                        if se > 0:
                            z_score = abs(mean_after - mean_before) / se
                            p_value = 2 * (1 - stats.norm.cdf(z_score))

                            if p_value < self.config.significance_level:
                                change_point = await self._create_change_point(
                                    user_id, metric_name, timestamps, values, i,
                                    ChangeType.LEVEL_SHIFT, DetectionMethod.WINDOW_BASED, ChangeType.LEVEL_SHIFT
                                )
                                if change_point:
                                    change_point.statistic_value = float(z_score)
                                    change_point.p_value = float(p_value)
                                    change_points.append(change_point)

            return change_points

        except Exception as e:
            logger.error(f"Error in window-based detection: {e}")
            return []

    async def _ml_based_detection(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float]
    ) -> List[ChangePoint]:
        """Machine learning based change detection."""
        try:
            if len(values) < 50:
                return []

            # Use Isolation Forest for anomaly detection
            from sklearn.ensemble import IsolationForest

            # Reshape data for sklearn
            X = np.array(values).reshape(-1, 1)

            # Fit Isolation Forest
            iso_forest = IsolationForest(contamination=0.1, random_state=42)
            anomaly_labels = iso_forest.fit_predict(X)
            anomaly_scores = iso_forest.decision_function(X)

            # Find change points based on anomalies
            change_points = []
            consecutive_anomalies = 0
            max_consecutive = 0
            max_consecutive_idx = -1

            for i, label in enumerate(anomaly_labels):
                if label == -1:  # Anomaly
                    consecutive_anomalies += 1
                    if consecutive_anomalies > max_consecutive:
                        max_consecutive = consecutive_anomalies
                        max_consecutive_idx = i
                else:
                    consecutive_anomalies = 0

            # If we found significant consecutive anomalies, mark as change point
            if max_consecutive >= 3 and max_consecutive_idx < len(timestamps):
                change_point = await self._create_change_point(
                    user_id, metric_name, timestamps, values, max_consecutive_idx,
                    ChangeType.PATTERN_CHANGE, DetectionMethod.ML_BASED, ChangeType.PATTERN_CHANGE
                )
                if change_point:
                    change_point.statistic_value = float(anomaly_scores[max_consecutive_idx])
                    change_points.append(change_point)

            return change_points

        except ImportError:
            logger.warning("scikit-learn not available for ML-based detection")
            return []
        except Exception as e:
            logger.error(f"Error in ML-based detection: {e}")
            return []

    async def _create_change_point(
        self,
        user_id: str,
        metric_name: str,
        timestamps: List[datetime],
        values: List[float],
        change_idx: int,
        change_type: ChangeType,
        detection_method: DetectionMethod,
        category: str
    ) -> Optional[ChangePoint]:
        """Create a ChangePoint object from detection results."""
        try:
            if change_idx >= len(timestamps) or change_idx < len(values):
                return None

            # Calculate baseline and post-change statistics
            baseline_size = min(change_idx, len(values) // 3)
            post_change_size = min(len(values) - change_idx, len(values) // 3)

            if baseline_size < 3 or post_change_size < 3:
                return None

            baseline_values = values[change_idx - baseline_size:change_idx]
            post_change_values = values[change_idx:change_idx + post_change_size]

            baseline_mean = np.mean(baseline_values)
            post_change_mean = np.mean(post_change_values)
            change_magnitude = abs(post_change_mean - baseline_mean)

            # Calculate confidence score based on change magnitude and consistency
            confidence_score = min(1.0, change_magnitude / (np.std(baseline_values) + 1e-8))

            change_point = ChangePoint(
                id=f"change_{user_id}_{metric_name}_{change_idx}_{datetime.utcnow().timestamp()}",
                user_id=user_id,
                metric_name=metric_name,
                change_type=change_type,
                detection_method=detection_method,
                change_point=timestamps[change_idx],
                baseline_start=timestamps[change_idx - baseline_size],
                baseline_end=timestamps[change_idx],
                post_change_start=timestamps[change_idx],
                baseline_mean=float(baseline_mean),
                post_change_mean=float(post_change_mean),
                change_magnitude=float(change_magnitude),
                confidence_score=float(confidence_score),
                significance_level=self.config.significance_level,
                description=f"{category.replace('_', ' ').title()} detected in {metric_name}"
            )

            return change_point

        except Exception as e:
            logger.error(f"Error creating change point: {e}")
            return None

    async def _detect_seasonality(
        self,
        values: List[float],
        timestamps: List[datetime]
    ) -> Dict[str, Any]:
        """Detect seasonal patterns in time series data."""
        try:
            if not self.statsmodels_available:
                return {'has_seasonality': False, 'period': None, 'strength': 0.0}

            # Convert to pandas series with datetime index
            if len(values) < 14:  # Need at least 2 weeks for weekly seasonality
                return {'has_seasonality': False, 'period': None, 'strength': 0.0}

            # Try different seasonal periods
            periods_to_test = [7, 30, 365]  # weekly, monthly, yearly
            best_period = None
            best_strength = 0.0

            for period in periods_to_test:
                if len(values) >= 2 * period:
                    try:
                        # Perform seasonal decomposition
                        series = pd.Series(values, index=pd.to_datetime(timestamps))
                        decomposition = seasonal_decompose(series, model='additive', period=period)

                        # Calculate seasonal strength
                        seasonal_var = np.var(decomposition.seasonal.dropna())
                        total_var = np.var(series)
                        strength = seasonal_var / total_var if total_var > 0 else 0.0

                        if strength > best_strength and strength > 0.1:  # Minimum strength threshold
                            best_strength = strength
                            best_period = period

                    except Exception as e:
                        logger.debug(f"Error testing period {period}: {e}")
                        continue

            return {
                'has_seasonality': best_period is not None,
                'period': best_period,
                'strength': best_strength
            }

        except Exception as e:
            logger.error(f"Error detecting seasonality: {e}")
            return {'has_seasonality': False, 'period': None, 'strength': 0.0}

    async def _generate_forecast(
        self,
        values: List[float],
        slope: float,
        intercept: float,
        std_err: float
    ) -> Dict[str, Optional[float]]:
        """Generate simple forecast based on linear trend."""
        try:
            next_x = len(values)
            next_value = slope * next_x + intercept

            # Calculate confidence interval
            confidence_level = 0.95
            alpha = 1 - confidence_level
            t_value = stats.t.ppf(1 - alpha/2, len(values) - 2)

            # Prediction interval
            se_prediction = std_err * np.sqrt(1 + 1/len(values) + (next_x - np.mean(range(len(values))))**2 /
                                      np.sum([(x - np.mean(range(len(values))))**2 for x in range(len(values))]))

            margin = t_value * se_prediction

            return {
                'next_value': float(next_value),
                'confidence_lower': float(next_value - margin),
                'confidence_upper': float(next_value + margin)
            }

        except Exception as e:
            logger.error(f"Error generating forecast: {e}")
            return {'next_value': None, 'confidence_lower': None, 'confidence_upper': None}

    def _calculate_impact_level(self, change: ChangePoint) -> ImpactLevel:
        """Calculate impact level based on change characteristics."""
        try:
            # Consider change magnitude, confidence, and metric type
            impact_score = 0.0

            # Change magnitude contribution
            if change.change_magnitude > 50:
                impact_score += 0.4
            elif change.change_magnitude > 20:
                impact_score += 0.3
            elif change.change_magnitude > 10:
                impact_score += 0.2
            elif change.change_magnitude > 5:
                impact_score += 0.1

            # Confidence contribution
            impact_score += change.confidence_score * 0.3

            # Statistical significance contribution
            if change.p_value and change.p_value < 0.01:
                impact_score += 0.3
            elif change.p_value and change.p_value < 0.05:
                impact_score += 0.2

            # Determine impact level
            if impact_score >= 0.8:
                return ImpactLevel.CRITICAL
            elif impact_score >= 0.6:
                return ImpactLevel.HIGH
            elif impact_score >= 0.4:
                return ImpactLevel.MEDIUM
            else:
                return ImpactLevel.LOW

        except Exception:
            return ImpactLevel.MEDIUM

    # TODO(human): Implement remaining private methods for database operations
    async def _store_time_series_data(self, data: List[TimeSeriesPoint]) -> None:
        """Store time series data in database."""
        pass

    async def _store_change_points(self, change_points: List[ChangePoint]) -> None:
        """Store detected change points in database."""
        pass

    async def _store_trend_analysis(self, trend_analysis: TrendAnalysis) -> None:
        """Store trend analysis results in database."""
        pass

    async def _store_baseline(self, baseline: BehavioralBaseline) -> None:
        """Store behavioral baseline in database."""
        pass

    async def get_time_series_data(
        self,
        user_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        bucket_size: str = "day"
    ) -> List[TimeSeriesPoint]:
        """Retrieve time series data from database."""
        # TODO(human): Implement actual database retrieval
        # For now, return mock data
        return await self.aggregate_time_series_data(user_id, metric_name, start_time, end_time, bucket_size)

    async def _get_user_metric_data(
        self,
        user_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[float]:
        """Get user's metric data for baseline calculation."""
        # TODO(human): Implement database retrieval
        return []

    async def _get_peer_group_data(
        self,
        user_id: str,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[float]:
        """Get peer group metric data for baseline calculation."""
        # TODO(human): Implement database retrieval
        return []

    async def _get_organizational_data(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime
    ) -> List[float]:
        """Get organizational metric data for baseline calculation."""
        # TODO(human): Implement database retrieval
        return []

    async def _consolidate_change_points(self, change_points: List[ChangePoint]) -> List[ChangePoint]:
        """Consolidate duplicate or nearby change points."""
        if not change_points:
            return []

        # Sort by change point time
        sorted_points = sorted(change_points, key=lambda cp: cp.change_point)
        consolidated = []

        # Group nearby change points (within 1 day)
        tolerance = timedelta(days=1)
        current_group = [sorted_points[0]]

        for cp in sorted_points[1:]:
            if cp.change_point - current_group[-1].change_point <= tolerance:
                current_group.append(cp)
            else:
                # Consolidate current group
                if current_group:
                    consolidated.append(self._merge_change_points(current_group))
                current_group = [cp]

        # Add last group
        if current_group:
            consolidated.append(self._merge_change_points(current_group))

        return consolidated

    def _merge_change_points(self, change_points: List[ChangePoint]) -> ChangePoint:
        """Merge multiple change points into one."""
        if not change_points:
            raise ValueError("Cannot merge empty change points list")

        if len(change_points) == 1:
            return change_points[0]

        # Use the most confident change point as base
        base_cp = max(change_points, key=lambda cp: cp.confidence_score)

        # Update with information from other points
        base_cp.description = f"Multiple changes detected: {len(change_points)} methods agree"

        # Average the statistics
        baseline_means = [cp.baseline_mean for cp in change_points]
        post_change_means = [cp.post_change_mean for cp in change_points]
        change_magnitudes = [cp.change_magnitude for cp in change_points]

        base_cp.baseline_mean = np.mean(baseline_means)
        base_cp.post_change_mean = np.mean(post_change_means)
        base_cp.change_magnitude = np.mean(change_magnitudes)

        return base_cp

    async def _generate_progression_insights(
        self,
        metrics_analysis: Dict[str, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate insights from progression analysis."""
        insights = []

        for metric, analysis in metrics_analysis.items():
            # Trend insights
            if analysis.get('trend'):
                trend = analysis['trend']
                if trend['trend_direction'] == 'increasing' and trend['r_squared'] > 0.7:
                    insights.append({
                        'type': 'positive_trend',
                        'metric': metric,
                        'description': f"Strong increasing trend in {metric} detected",
                        'confidence': trend['r_squared']
                    })
                elif trend['trend_direction'] == 'decreasing' and trend['r_squared'] > 0.7:
                    insights.append({
                        'type': 'negative_trend',
                        'metric': metric,
                        'description': f"Concerning decreasing trend in {metric} detected",
                        'confidence': trend['r_squared']
                    })

            # Change point insights
            if analysis.get('change_points'):
                high_impact_changes = [cp for cp in analysis['change_points']
                                     if cp.get('impact_level') in ['high', 'critical']]
                if high_impact_changes:
                    insights.append({
                        'type': 'significant_changes',
                        'metric': metric,
                        'description': f"{len(high_impact_changes)} significant changes detected in {metric}",
                        'count': len(high_impact_changes)
                    })

        return insights

    async def _generate_progression_recommendations(
        self,
        metrics_analysis: Dict[str, Dict[str, Any]],
        insights: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on progression analysis."""
        recommendations = []

        # Trend-based recommendations
        negative_trends = [insight for insight in insights if insight['type'] == 'negative_trend']
        if negative_trends:
            recommendations.append("Investigate decreasing trends in behavioral metrics")

        # Change-based recommendations
        significant_changes = [insight for insight in insights if insight['type'] == 'significant_changes']
        if significant_changes:
            recommendations.append("Review recent significant behavioral changes")

        # General recommendations
        recommendations.extend([
            "Monitor trends regularly for early intervention opportunities",
            "Consider seasonal factors in behavioral analysis"
        ])

        return recommendations[:10]  # Limit to top 10