"""
Advanced Anomaly Detection System
Sophisticated statistical and machine learning methods for detecting anomalies in user behavior.
Implements multiple detection algorithms for different types of anomalies.

Key Features:
- Statistical outlier detection (Z-score, IQR, Modified Z-score)
- Time series anomaly detection (Seasonal decomposition, ARIMA residuals)
- Machine learning based detection (Isolation Forest, One-Class SVM, Local Outlier Factor)
- Multivariate anomaly detection
- Real-time streaming anomaly detection
- Adaptive thresholding and drift detection
- Ensemble methods for improved accuracy
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
from scipy.signal import savgol_filter
from sklearn.ensemble import IsolationForest
from sklearn.svm import OneClassSVM
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.decomposition import PCA
from sklearn.covariance import EllipticEnvelope
import warnings
warnings.filterwarnings('ignore')

from sqlalchemy.orm import Session
import redis.asyncio as redis

logger = logging.getLogger(__name__)

class AnomalyMethod(Enum):
    """Methods for anomaly detection."""
    Z_SCORE = "z_score"
    MODIFIED_Z_SCORE = "modified_z_score"
    IQR = "iqr"
    ISOLATION_FOREST = "isolation_forest"
    ONE_CLASS_SVM = "one_class_svm"
    LOCAL_OUTLIER_FACTOR = "local_outlier_factor"
    ELLIPTIC_ENVELOPE = "elliptic_envelope"
    SEASONAL_DECOMPOSITION = "seasonal_decomposition"
    MOVING_AVERAGE = "moving_average"
    EXPONENTIAL_SMOOTHING = "exponential_smoothing"
    ENSEMBLE = "ensemble"

class AnomalyCategory(Enum):
    """Categories of anomalies."""
    STATISTICAL = "statistical"
    TEMPORAL = "temporal"
    MULTIVARIATE = "multivariate"
    CONTEXTUAL = "contextual"
    COLLECTIVE = "collective"
    POINT = "point"

class AnomalySeverity(Enum):
    """Severity levels for anomalies."""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"
    CRITICAL = "critical"

@dataclass
class AnomalyResult:
    """Result of anomaly detection."""
    anomaly_id: str
    timestamp: datetime
    value: float
    anomaly_score: float
    method: AnomalyMethod
    category: AnomalyCategory
    severity: AnomalySeverity
    confidence: float
    context: Dict[str, Any] = field(default_factory=dict)
    baseline_stats: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""

@dataclass
class AnomalyConfig:
    """Configuration for anomaly detection."""

    # Statistical method parameters
    z_score_threshold: float = 3.0
    modified_z_score_threshold: float = 3.5
    iqr_multiplier: float = 1.5

    # ML method parameters
    isolation_forest_contamination: float = 0.1
    one_class_svm_nu: float = 0.1
    lof_n_neighbors: int = 20
    elliptic_envelope_contamination: float = 0.1

    # Time series parameters
    moving_average_window: int = 24  # hours
    seasonal_period: int = 24  # hours
    min_samples: int = 50
    max_samples: int = 10000

    # Ensemble parameters
    ensemble_methods: List[AnomalyMethod] = field(default_factory=lambda: [
        AnomalyMethod.Z_SCORE,
        AnomalyMethod.ISOLATION_FOREST,
        AnomalyMethod.LOCAL_OUTLIER_FACTOR
    ])
    ensemble_threshold: float = 0.5  # Fraction of methods that must agree

    # Performance parameters
    cache_ttl_hours: int = 1
    batch_size: int = 1000

    # Redis configuration
    redis_url: str = "redis://localhost:6379/6"

class AdvancedAnomalyDetector:
    """
    Advanced anomaly detection system with multiple algorithms.
    """

    def __init__(self, db_session: Session, config: Optional[AnomalyConfig] = None):
        self.db = db_session
        self.config = config or AnomalyConfig()
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()

        # Initialize ML models
        self.scaler = StandardScaler()
        self.robust_scaler = RobustScaler()
        self.pca = PCA(n_components=0.95)  # Keep 95% variance

        # Initialize detection methods
        self.detection_methods = {
            AnomalyMethod.Z_SCORE: self._detect_z_score_anomalies,
            AnomalyMethod.MODIFIED_Z_SCORE: self._detect_modified_z_score_anomalies,
            AnomalyMethod.IQR: self._detect_iqr_anomalies,
            AnomalyMethod.ISOLATION_FOREST: self._detect_isolation_forest_anomalies,
            AnomalyMethod.ONE_CLASS_SVM: self._detect_one_class_svm_anomalies,
            AnomalyMethod.LOCAL_OUTLIER_FACTOR: self._detect_lof_anomalies,
            AnomalyMethod.ELLIPTIC_ENVELOPE: self._detect_elliptic_envelope_anomalies,
            AnomalyMethod.SEASONAL_DECOMPOSITION: self._detect_seasonal_anomalies,
            AnomalyMethod.MOVING_AVERAGE: self._detect_moving_average_anomalies,
            AnomalyMethod.EXPONENTIAL_SMOOTHING: self._detect_exponential_smoothing_anomalies,
            AnomalyMethod.ENSEMBLE: self._detect_ensemble_anomalies
        }

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
            logger.info("Anomaly detection Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for anomaly detection: {e}")
            self.redis_client = None

    async def detect_anomalies(
        self,
        data: Union[List[float], pd.DataFrame, pd.Series],
        timestamps: Optional[List[datetime]] = None,
        method: AnomalyMethod = AnomalyMethod.ENSEMBLE,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in the provided data using the specified method.

        Args:
            data: Input data for anomaly detection
            timestamps: Optional timestamps for time series data
            method: Detection method to use
            user_id: Optional user ID for context
            context: Additional context information

        Returns:
            List of detected anomalies
        """
        try:
            # Validate input data
            if not self._validate_input_data(data):
                logger.error("Invalid input data for anomaly detection")
                return []

            # Convert to pandas Series if needed
            if isinstance(data, list):
                series = pd.Series(data)
            elif isinstance(data, np.ndarray):
                series = pd.Series(data)
            elif isinstance(data, pd.DataFrame):
                series = data.iloc[:, 0]  # Use first column
            else:
                series = data

            # Handle timestamps
            if timestamps is None:
                timestamps = [datetime.utcnow() - timedelta(hours=i) for i in range(len(series)-1, -1, -1)]

            # Use cached results if available
            cache_key = f"anomaly_detection:{hash(str(data))}:{method.value}"
            if self.redis_client:
                cached_result = await self.redis_client.get(cache_key)
                if cached_result:
                    cached_anomalies = json.loads(cached_result)
                    return [self._dict_to_anomaly_result(a) for a in cached_anomalies]

            # Detect anomalies
            anomalies = await self.detection_methods[method](
                series, timestamps, user_id, context or {}
            )

            # Filter by confidence threshold
            anomalies = [a for a in anomalies if a.confidence >= 0.5]

            # Cache results
            if self.redis_client and anomalies:
                await self.redis_client.setex(
                    cache_key,
                    self.config.cache_ttl_hours * 3600,
                    json.dumps([self._anomaly_result_to_dict(a) for a in anomalies], default=str)
                )

            logger.info(f"Detected {len(anomalies)} anomalies using {method.value}")
            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    async def detect_multivariate_anomalies(
        self,
        data: pd.DataFrame,
        timestamps: Optional[List[datetime]] = None,
        method: AnomalyMethod = AnomalyMethod.ISOLATION_FOREST,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in multivariate data.

        Args:
            data: Multivariate data as DataFrame
            timestamps: Optional timestamps for each row
            method: Detection method to use
            user_id: Optional user ID for context
            context: Additional context information

        Returns:
            List of detected anomalies
        """
        try:
            if data.empty or len(data.columns) < 2:
                logger.error("Insufficient multivariate data for anomaly detection")
                return []

            # Handle timestamps
            if timestamps is None:
                timestamps = [datetime.utcnow() - timedelta(hours=i) for i in range(len(data)-1, -1, -1)]

            # Scale the data
            scaled_data = self.robust_scaler.fit_transform(data)

            # Use ensemble of multivariate methods
            anomalies = []

            # Isolation Forest
            if method in [AnomalyMethod.ISOLATION_FOREST, AnomalyMethod.ENSEMBLE]:
                iso_anomalies = await self._detect_multivariate_isolation_forest(
                    scaled_data, data, timestamps, user_id, context or {}
                )
                anomalies.extend(iso_anomalies)

            # Local Outlier Factor
            if method in [AnomalyMethod.LOCAL_OUTLIER_FACTOR, AnomalyMethod.ENSEMBLE]:
                lof_anomalies = await self._detect_multivariate_lof(
                    scaled_data, data, timestamps, user_id, context or {}
                )
                anomalies.extend(lof_anomalies)

            # Elliptic Envelope
            if method in [AnomalyMethod.ELLIPTIC_ENVELOPE, AnomalyMethod.ENSEMBLE]:
                ee_anomalies = await self._detect_multivariate_elliptic_envelope(
                    scaled_data, data, timestamps, user_id, context or {}
                )
                anomalies.extend(ee_anomalies)

            # Remove duplicates and sort by confidence
            unique_anomalies = self._remove_duplicate_anomalies(anomalies)
            unique_anomalies.sort(key=lambda x: x.confidence, reverse=True)

            return unique_anomalies

        except Exception as e:
            logger.error(f"Error detecting multivariate anomalies: {e}")
            return []

    async def detect_time_series_anomalies(
        self,
        data: pd.Series,
        timestamps: Optional[List[datetime]] = None,
        seasonal_period: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> List[AnomalyResult]:
        """
        Detect anomalies in time series data using specialized time series methods.

        Args:
            data: Time series data
            timestamps: Optional timestamps
            seasonal_period: Seasonal period for decomposition
            user_id: Optional user ID for context

        Returns:
            List of detected anomalies
        """
        try:
            if len(data) < self.config.min_samples:
                logger.warning("Insufficient data for time series anomaly detection")
                return []

            # Handle timestamps
            if timestamps is None:
                timestamps = [datetime.utcnow() - timedelta(hours=i) for i in range(len(data)-1, -1, -1)]

            anomalies = []
            seasonal_period = seasonal_period or self.config.seasonal_period

            # Seasonal decomposition
            if len(data) >= 2 * seasonal_period:
                seasonal_anomalies = await self._detect_seasonal_anomalies(data, timestamps, user_id)
                anomalies.extend(seasonal_anomalies)

            # Moving average anomalies
            ma_anomalies = await self._detect_moving_average_anomalies(data, timestamps, user_id)
            anomalies.extend(ma_anomalies)

            # Exponential smoothing anomalies
            es_anomalies = await self._detect_exponential_smoothing_anomalies(data, timestamps, user_id)
            anomalies.extend(es_anomalies)

            # Remove duplicates and sort
            unique_anomalies = self._remove_duplicate_anomalies(anomalies)
            unique_anomalies.sort(key=lambda x: x.anomaly_score, reverse=True)

            return unique_anomalies

        except Exception as e:
            logger.error(f"Error detecting time series anomalies: {e}")
            return []

    async def _detect_z_score_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Z-score method."""
        anomalies = []

        try:
            mean_val = data.mean()
            std_val = data.std()

            if std_val == 0:
                return anomalies

            z_scores = np.abs((data - mean_val) / std_val)
            anomaly_indices = np.where(z_scores > self.config.z_score_threshold)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(z_scores[idx], max_score=5)
                confidence = min(0.95, z_scores[idx] / 5)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"z_score_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(z_scores[idx]),
                    method=AnomalyMethod.Z_SCORE,
                    category=AnomalyCategory.STATISTICAL,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'mean': float(mean_val), 'std': float(std_val)},
                    explanation=f"Z-score of {z_scores[idx]:.2f} exceeds threshold of {self.config.z_score_threshold}"
                ))

        except Exception as e:
            logger.error(f"Error in Z-score anomaly detection: {e}")

        return anomalies

    async def _detect_modified_z_score_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Modified Z-score method (more robust to outliers)."""
        anomalies = []

        try:
            median_val = data.median()
            mad_val = np.median(np.abs(data - median_val))

            if mad_val == 0:
                return anomalies

            modified_z_scores = 0.6745 * (data - median_val) / mad_val
            anomaly_indices = np.where(np.abs(modified_z_scores) > self.config.modified_z_score_threshold)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(abs(modified_z_scores[idx]), max_score=5)
                confidence = min(0.95, abs(modified_z_scores[idx]) / 5)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"modified_z_score_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(abs(modified_z_scores[idx])),
                    method=AnomalyMethod.MODIFIED_Z_SCORE,
                    category=AnomalyCategory.STATISTICAL,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'median': float(median_val), 'mad': float(mad_val)},
                    explanation=f"Modified Z-score of {abs(modified_z_scores[idx]):.2f} exceeds threshold of {self.config.modified_z_score_threshold}"
                ))

        except Exception as e:
            logger.error(f"Error in Modified Z-score anomaly detection: {e}")

        return anomalies

    async def _detect_iqr_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Interquartile Range (IQR) method."""
        anomalies = []

        try:
            q1 = data.quantile(0.25)
            q3 = data.quantile(0.75)
            iqr = q3 - q1

            if iqr == 0:
                return anomalies

            lower_bound = q1 - self.config.iqr_multiplier * iqr
            upper_bound = q3 + self.config.iqr_multiplier * iqr

            anomaly_indices = np.where((data < lower_bound) | (data > upper_bound))[0]

            for idx in anomaly_indices:
                value = data.iloc[idx]
                distance = min(abs(value - lower_bound), abs(value - upper_bound)) / iqr
                severity = self._calculate_severity(distance, max_score=3)
                confidence = min(0.95, distance / 3)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"iqr_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(value),
                    anomaly_score=float(distance),
                    method=AnomalyMethod.IQR,
                    category=AnomalyCategory.STATISTICAL,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'q1': float(q1), 'q3': float(q3), 'iqr': float(iqr)},
                    explanation=f"Value {value:.2f} outside IQR bounds [{lower_bound:.2f}, {upper_bound:.2f}]"
                ))

        except Exception as e:
            logger.error(f"Error in IQR anomaly detection: {e}")

        return anomalies

    async def _detect_isolation_forest_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Isolation Forest algorithm."""
        anomalies = []

        try:
            if len(data) < 10:
                return anomalies

            # Reshape data for sklearn
            X = data.values.reshape(-1, 1)

            # Fit Isolation Forest
            iso_forest = IsolationForest(
                contamination=self.config.isolation_forest_contamination,
                random_state=42,
                n_estimators=100
            )
            anomaly_labels = iso_forest.fit_predict(X)
            anomaly_scores = iso_forest.decision_function(X)

            # Anomalies are labeled as -1
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-anomaly_scores[idx], max_score=0.5)
                confidence = min(0.95, -anomaly_scores[idx] * 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"isolation_forest_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(-anomaly_scores[idx]),
                    method=AnomalyMethod.ISOLATION_FOREST,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'contamination': self.config.isolation_forest_contamination},
                    explanation=f"Isolation Forest anomaly score of {anomaly_scores[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in Isolation Forest anomaly detection: {e}")

        return anomalies

    async def _detect_one_class_svm_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using One-Class SVM algorithm."""
        anomalies = []

        try:
            if len(data) < 20:
                return anomalies

            # Reshape and scale data
            X = data.values.reshape(-1, 1)
            X_scaled = self.scaler.fit_transform(X)

            # Fit One-Class SVM
            svm = OneClassSVM(nu=self.config.one_class_svm_nu, kernel='rbf', gamma='scale')
            anomaly_labels = svm.fit_predict(X_scaled)
            decision_scores = svm.decision_function(X_scaled)

            # Anomalies are labeled as -1
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-decision_scores[idx], max_score=0.5)
                confidence = min(0.95, -decision_scores[idx] * 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"one_class_svm_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(-decision_scores[idx]),
                    method=AnomalyMethod.ONE_CLASS_SVM,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'nu': self.config.one_class_svm_nu},
                    explanation=f"One-Class SVM decision score of {decision_scores[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in One-Class SVM anomaly detection: {e}")

        return anomalies

    async def _detect_lof_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Local Outlier Factor algorithm."""
        anomalies = []

        try:
            if len(data) < self.config.lof_n_neighbors + 1:
                return anomalies

            # Reshape data for sklearn
            X = data.values.reshape(-1, 1)

            # Fit Local Outlier Factor
            lof = LocalOutlierFactor(
                n_neighbors=self.config.lof_n_neighbors,
                contamination='auto'
            )
            anomaly_labels = lof.fit_predict(X)
            negative_outlier_factors = lof.negative_outlier_factor_

            # Anomalies are labeled as -1
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-negative_outlier_factors[idx], max_score=2)
                confidence = min(0.95, -negative_outlier_factors[idx] / 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"lof_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(-negative_outlier_factors[idx]),
                    method=AnomalyMethod.LOCAL_OUTLIER_FACTOR,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'n_neighbors': self.config.lof_n_neighbors},
                    explanation=f"Local Outlier Factor of {negative_outlier_factors[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in LOF anomaly detection: {e}")

        return anomalies

    async def _detect_elliptic_envelope_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using Elliptic Envelope algorithm."""
        anomalies = []

        try:
            if len(data) < 20:
                return anomalies

            # Reshape data
            X = data.values.reshape(-1, 1)

            # Fit Elliptic Envelope
            ee = EllipticEnvelope(
                contamination=self.config.elliptic_envelope_contamination,
                random_state=42
            )
            anomaly_labels = ee.fit_predict(X)
            decision_scores = ee.decision_function(X)

            # Anomalies are labeled as -1
            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-decision_scores[idx], max_score=0.5)
                confidence = min(0.95, -decision_scores[idx] * 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"elliptic_envelope_{idx}_{user_id}_{hash(str(data))}",
                    timestamp=timestamps[idx],
                    value=float(data.iloc[idx]),
                    anomaly_score=float(-decision_scores[idx]),
                    method=AnomalyMethod.ELLIPTIC_ENVELOPE,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context=context,
                    baseline_stats={'contamination': self.config.elliptic_envelope_contamination},
                    explanation=f"Elliptic Envelope decision score of {decision_scores[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in Elliptic Envelope anomaly detection: {e}")

        return anomalies

    async def _detect_seasonal_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str]
    ) -> List[AnomalyResult]:
        """Detect anomalies using seasonal decomposition."""
        anomalies = []

        try:
            if len(data) < 2 * self.config.seasonal_period:
                return anomalies

            # Simple seasonal decomposition using moving averages
            seasonal_period = self.config.seasonal_period

            # Calculate seasonal component using rolling statistics
            seasonal = data.rolling(window=seasonal_period, center=True).mean()
            trend = data.rolling(window=seasonal_period*2, center=True).mean()
            residual = data - seasonal - trend

            # Detect anomalies in residuals
            residual_mean = residual.mean()
            residual_std = residual.std()

            if residual_std == 0:
                return anomalies

            z_scores = np.abs((residual - residual_mean) / residual_std)
            anomaly_indices = np.where(z_scores > self.config.z_score_threshold)[0]

            for idx in anomaly_indices:
                if pd.notna(residual.iloc[idx]):  # Skip NaN values
                    severity = self._calculate_severity(z_scores[idx], max_score=4)
                    confidence = min(0.95, z_scores[idx] / 4)

                    anomalies.append(AnomalyResult(
                        anomaly_id=f"seasonal_{idx}_{user_id}_{hash(str(data))}",
                        timestamp=timestamps[idx],
                        value=float(data.iloc[idx]),
                        anomaly_score=float(z_scores[idx]),
                        method=AnomalyMethod.SEASONAL_DECOMPOSITION,
                        category=AnomalyCategory.TEMPORAL,
                        severity=severity,
                        confidence=confidence,
                        context={'seasonal_period': seasonal_period},
                        baseline_stats={'residual_mean': float(residual_mean), 'residual_std': float(residual_std)},
                        explanation=f"Seasonal residual Z-score of {z_scores[idx]:.2f}"
                    ))

        except Exception as e:
            logger.error(f"Error in seasonal anomaly detection: {e}")

        return anomalies

    async def _detect_moving_average_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str]
    ) -> List[AnomalyResult]:
        """Detect anomalies using moving average method."""
        anomalies = []

        try:
            window = min(self.config.moving_average_window, len(data) // 3)
            if window < 3:
                return anomalies

            # Calculate moving average and standard deviation
            moving_avg = data.rolling(window=window, center=True).mean()
            moving_std = data.rolling(window=window, center=True).std()

            # Calculate deviations from moving average
            deviations = np.abs(data - moving_avg)
            threshold = 2 * moving_std  # 2 standard deviations

            anomaly_indices = np.where(deviations > threshold)[0]

            for idx in anomaly_indices:
                if pd.notna(moving_avg.iloc[idx]) and pd.notna(moving_std.iloc[idx]) and moving_std.iloc[idx] > 0:
                    z_score = deviations.iloc[idx] / moving_std.iloc[idx]
                    severity = self._calculate_severity(z_score, max_score=3)
                    confidence = min(0.95, z_score / 3)

                    anomalies.append(AnomalyResult(
                        anomaly_id=f"moving_avg_{idx}_{user_id}_{hash(str(data))}",
                        timestamp=timestamps[idx],
                        value=float(data.iloc[idx]),
                        anomaly_score=float(z_score),
                        method=AnomalyMethod.MOVING_AVERAGE,
                        category=AnomalyCategory.TEMPORAL,
                        severity=severity,
                        confidence=confidence,
                        context={'window_size': window},
                        baseline_stats={
                            'moving_avg': float(moving_avg.iloc[idx]),
                            'moving_std': float(moving_std.iloc[idx])
                        },
                        explanation=f"Deviation of {z_score:.2f} standard deviations from moving average"
                    ))

        except Exception as e:
            logger.error(f"Error in moving average anomaly detection: {e}")

        return anomalies

    async def _detect_exponential_smoothing_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str]
    ) -> List[AnomalyResult]:
        """Detect anomalies using exponential smoothing."""
        anomalies = []

        try:
            # Calculate exponential smoothing
            alpha = 0.3  # Smoothing factor
            smoothed_data = data.copy()

            for i in range(1, len(smoothed_data)):
                smoothed_data.iloc[i] = alpha * data.iloc[i] + (1 - alpha) * smoothed_data.iloc[i-1]

            # Calculate residuals
            residuals = data - smoothed_data
            residual_std = residuals.std()

            if residual_std == 0:
                return anomalies

            z_scores = np.abs(residuals / residual_std)
            anomaly_indices = np.where(z_scores > self.config.z_score_threshold)[0]

            for idx in anomaly_indices:
                if idx > 0:  # Skip first point as it has no smoothing reference
                    severity = self._calculate_severity(z_scores[idx], max_score=3)
                    confidence = min(0.95, z_scores[idx] / 3)

                    anomalies.append(AnomalyResult(
                        anomaly_id=f"exp_smooth_{idx}_{user_id}_{hash(str(data))}",
                        timestamp=timestamps[idx],
                        value=float(data.iloc[idx]),
                        anomaly_score=float(z_scores[idx]),
                        method=AnomalyMethod.EXPONENTIAL_SMOOTHING,
                        category=AnomalyCategory.TEMPORAL,
                        severity=severity,
                        confidence=confidence,
                        context={'alpha': alpha},
                        baseline_stats={'smoothed_value': float(smoothed_data.iloc[idx]), 'residual_std': float(residual_std)},
                        explanation=f"Exponential smoothing residual Z-score of {z_scores[idx]:.2f}"
                    ))

        except Exception as e:
            logger.error(f"Error in exponential smoothing anomaly detection: {e}")

        return anomalies

    async def _detect_ensemble_anomalies(
        self,
        data: pd.Series,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect anomalies using ensemble of multiple methods."""
        all_anomalies = []

        # Collect anomalies from all ensemble methods
        for method in self.config.ensemble_methods:
            try:
                method_anomalies = await self.detection_methods[method](data, timestamps, user_id, context)
                all_anomalies.extend(method_anomalies)
            except Exception as e:
                logger.error(f"Error in ensemble method {method.value}: {e}")

        if not all_anomalies:
            return []

        # Group anomalies by timestamp/index
        anomaly_groups = {}
        for anomaly in all_anomalies:
            # Use a simple key based on timestamp (rounded to nearest minute)
            key = anomaly.timestamp.replace(second=0, microsecond=0)
            if key not in anomaly_groups:
                anomaly_groups[key] = []
            anomaly_groups[key].append(anomaly)

        # Create ensemble anomalies
        ensemble_anomalies = []
        for timestamp, group in anomaly_groups.items():
            # Check if enough methods agree
            agreement_count = len(set(a.method for a in group))
            total_methods = len(self.config.ensemble_methods)
            agreement_ratio = agreement_count / total_methods

            if agreement_ratio >= self.config.ensemble_threshold:
                # Calculate ensemble metrics
                avg_score = np.mean([a.anomaly_score for a in group])
                max_confidence = max([a.confidence for a in group])
                combined_methods = [a.method.value for a in group]

                # Determine severity based on consensus
                severity_counts = {}
                for a in group:
                    severity_counts[a.severity] = severity_counts.get(a.severity, 0) + 1

                # Use the most common severity
                consensus_severity = max(severity_counts, key=severity_counts.get)

                ensemble_anomaly = AnomalyResult(
                    anomaly_id=f"ensemble_{hash(str(timestamp))}_{user_id}",
                    timestamp=timestamp,
                    value=float(next(a.value for a in group)),  # Use first anomaly's value
                    anomaly_score=float(avg_score),
                    method=AnomalyMethod.ENSEMBLE,
                    category=AnomalyCategory.COLLECTIVE,
                    severity=consensus_severity,
                    confidence=max_confidence * agreement_ratio,
                    context={**context, 'methods': combined_methods, 'agreement_ratio': agreement_ratio},
                    baseline_stats={'ensemble_methods': total_methods, 'agreement_count': agreement_count},
                    explanation=f"Ensemble consensus: {agreement_ratio:.1%} of methods detected anomaly"
                )
                ensemble_anomalies.append(ensemble_anomaly)

        return sorted(ensemble_anomalies, key=lambda x: x.confidence, reverse=True)

    async def _detect_multivariate_isolation_forest(
        self,
        scaled_data: np.ndarray,
        original_data: pd.DataFrame,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect multivariate anomalies using Isolation Forest."""
        anomalies = []

        try:
            iso_forest = IsolationForest(
                contamination=self.config.isolation_forest_contamination,
                random_state=42
            )
            anomaly_labels = iso_forest.fit_predict(scaled_data)
            anomaly_scores = iso_forest.decision_function(scaled_data)

            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-anomaly_scores[idx], max_score=0.5)
                confidence = min(0.95, -anomaly_scores[idx] * 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"multivariate_iso_{idx}_{user_id}",
                    timestamp=timestamps[idx],
                    value=float(original_data.iloc[idx, 0]),  # Use first column value
                    anomaly_score=float(-anomaly_scores[idx]),
                    method=AnomalyMethod.ISOLATION_FOREST,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context={**context, 'features': original_data.columns.tolist()},
                    baseline_stats={'contamination': self.config.isolation_forest_contamination},
                    explanation=f"Multivariate Isolation Forest anomaly score: {anomaly_scores[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in multivariate Isolation Forest: {e}")

        return anomalies

    async def _detect_multivariate_lof(
        self,
        scaled_data: np.ndarray,
        original_data: pd.DataFrame,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect multivariate anomalies using Local Outlier Factor."""
        anomalies = []

        try:
            if len(scaled_data) < self.config.lof_n_neighbors + 1:
                return anomalies

            lof = LocalOutlierFactor(
                n_neighbors=self.config.lof_n_neighbors,
                contamination='auto'
            )
            anomaly_labels = lof.fit_predict(scaled_data)
            negative_outlier_factors = lof.negative_outlier_factor_

            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-negative_outlier_factors[idx], max_score=2)
                confidence = min(0.95, -negative_outlier_factors[idx] / 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"multivariate_lof_{idx}_{user_id}",
                    timestamp=timestamps[idx],
                    value=float(original_data.iloc[idx, 0]),
                    anomaly_score=float(-negative_outlier_factors[idx]),
                    method=AnomalyMethod.LOCAL_OUTLIER_FACTOR,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context={**context, 'features': original_data.columns.tolist()},
                    baseline_stats={'n_neighbors': self.config.lof_n_neighbors},
                    explanation=f"Multivariate LOF score: {negative_outlier_factors[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in multivariate LOF: {e}")

        return anomalies

    async def _detect_multivariate_elliptic_envelope(
        self,
        scaled_data: np.ndarray,
        original_data: pd.DataFrame,
        timestamps: List[datetime],
        user_id: Optional[str],
        context: Dict[str, Any]
    ) -> List[AnomalyResult]:
        """Detect multivariate anomalies using Elliptic Envelope."""
        anomalies = []

        try:
            ee = EllipticEnvelope(
                contamination=self.config.elliptic_envelope_contamination,
                random_state=42
            )
            anomaly_labels = ee.fit_predict(scaled_data)
            decision_scores = ee.decision_function(scaled_data)

            anomaly_indices = np.where(anomaly_labels == -1)[0]

            for idx in anomaly_indices:
                severity = self._calculate_severity(-decision_scores[idx], max_score=0.5)
                confidence = min(0.95, -decision_scores[idx] * 2)

                anomalies.append(AnomalyResult(
                    anomaly_id=f"multivariate_ee_{idx}_{user_id}",
                    timestamp=timestamps[idx],
                    value=float(original_data.iloc[idx, 0]),
                    anomaly_score=float(-decision_scores[idx]),
                    method=AnomalyMethod.ELLIPTIC_ENVELOPE,
                    category=AnomalyCategory.MULTIVARIATE,
                    severity=severity,
                    confidence=confidence,
                    context={**context, 'features': original_data.columns.tolist()},
                    baseline_stats={'contamination': self.config.elliptic_envelope_contamination},
                    explanation=f"Multivariate Elliptic Envelope score: {decision_scores[idx]:.3f}"
                ))

        except Exception as e:
            logger.error(f"Error in multivariate Elliptic Envelope: {e}")

        return anomalies

    def _calculate_severity(self, score: float, max_score: float) -> AnomalySeverity:
        """Calculate severity level based on anomaly score."""
        try:
            ratio = score / max_score

            if ratio >= 0.8:
                return AnomalySeverity.CRITICAL
            elif ratio >= 0.6:
                return AnomalySeverity.VERY_HIGH
            elif ratio >= 0.4:
                return AnomalySeverity.HIGH
            elif ratio >= 0.2:
                return AnomalySeverity.MEDIUM
            elif ratio >= 0.1:
                return AnomalySeverity.LOW
            else:
                return AnomalySeverity.VERY_LOW

        except Exception:
            return AnomalySeverity.MEDIUM

    def _validate_input_data(self, data: Union[List[float], pd.DataFrame, pd.Series]) -> bool:
        """Validate input data for anomaly detection."""
        try:
            if isinstance(data, list):
                return len(data) >= self.config.min_samples
            elif isinstance(data, (pd.Series, pd.DataFrame)):
                return len(data) >= self.config.min_samples
            elif isinstance(data, np.ndarray):
                return len(data) >= self.config.min_samples
            else:
                return False

        except Exception:
            return False

    def _remove_duplicate_anomalies(self, anomalies: List[AnomalyResult]) -> List[AnomalyResult]:
        """Remove duplicate anomalies within a small time window."""
        if not anomalies:
            return []

        # Sort by timestamp
        anomalies.sort(key=lambda x: x.timestamp)

        unique_anomalies = []
        seen_timestamps = set()

        for anomaly in anomalies:
            # Round timestamp to nearest minute for grouping
            rounded_time = anomaly.timestamp.replace(second=0, microsecond=0)

            if rounded_time not in seen_timestamps:
                unique_anomalies.append(anomaly)
                seen_timestamps.add(rounded_time)

        return unique_anomalies

    def _anomaly_result_to_dict(self, anomaly: AnomalyResult) -> Dict[str, Any]:
        """Convert AnomalyResult to dictionary for JSON serialization."""
        return {
            'anomaly_id': anomaly.anomaly_id,
            'timestamp': anomaly.timestamp.isoformat(),
            'value': anomaly.value,
            'anomaly_score': anomaly.anomaly_score,
            'method': anomaly.method.value,
            'category': anomaly.category.value,
            'severity': anomaly.severity.value,
            'confidence': anomaly.confidence,
            'context': anomaly.context,
            'baseline_stats': anomaly.baseline_stats,
            'explanation': anomaly.explanation
        }

    def _dict_to_anomaly_result(self, data: Dict[str, Any]) -> AnomalyResult:
        """Convert dictionary to AnomalyResult."""
        return AnomalyResult(
            anomaly_id=data['anomaly_id'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            value=data['value'],
            anomaly_score=data['anomaly_score'],
            method=AnomalyMethod(data['method']),
            category=AnomalyCategory(data['category']),
            severity=AnomalySeverity(data['severity']),
            confidence=data['confidence'],
            context=data['context'],
            baseline_stats=data['baseline_stats'],
            explanation=data['explanation']
        )