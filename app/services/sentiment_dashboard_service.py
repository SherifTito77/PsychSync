"""
Sentiment Trends Dashboard Service
Provides comprehensive sentiment analysis and trend visualization
data for interactive dashboards and reporting.
"""

import json
import logging
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

import numpy as np
from sklearn.preprocessing import StandardScaler

from app.services.nlp_service import NLPService, SentimentLabel
from app.services.theme_extraction_service import ThemeExtractionService

logger = logging.getLogger(__name__)


class TrendAnalysisPeriod(Enum):
    """Time periods for trend analysis"""

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class SentimentMetric(Enum):
    """Types of sentiment metrics"""

    POLARITY = "polarity"  # Overall sentiment score (-1 to 1)
    SUBJECTIVITY = "subjectivity"  # Subjectivity score (0 to 1)
    CONFIDENCE = "confidence"  # Analysis confidence (0 to 1)
    EMOTIONAL_INTENSITY = "emotional_intensity"  # Strength of emotions
    SENTIMENT_VOLATILITY = "sentiment_volatility"  # Variation in sentiment


class TrendDirection(Enum):
    """Trend direction classifications"""

    STRONGLY_IMPROVING = "strongly_improving"
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"
    STRONGLY_DECLINING = "strongly_declining"
    VOLATILE = "volatile"


@dataclass
class SentimentDataPoint:
    """Single sentiment data point"""

    timestamp: datetime
    sentiment_score: float
    sentiment_label: SentimentLabel
    confidence: float
    subjectivity: float
    text_sample: str
    metadata: dict[str, Any] = field(default_factory=dict)
    user_id: str | None = None
    session_id: str | None = None
    theme_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label.value,
            "confidence": self.confidence,
            "subjectivity": self.subjectivity,
            "text_sample": (
                self.text_sample[:100] + "..."
                if len(self.text_sample) > 100
                else self.text_sample
            ),
            "metadata": self.metadata,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "theme_ids": self.theme_ids,
        }


@dataclass
class SentimentTrend:
    """Sentiment trend analysis"""

    metric: SentimentMetric
    period: TrendAnalysisPeriod
    direction: TrendDirection
    strength: float  # 0-1 scale
    slope: float  # Linear regression slope
    volatility: float  # Standard deviation
    data_points: list[SentimentDataPoint] = field(default_factory=list)
    predictions: list[tuple[datetime, float]] = field(default_factory=list)
    confidence_interval: tuple[float, float] = (0.0, 0.0)
    seasonal_pattern: bool = False
    anomaly_detected: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric.value,
            "period": self.period.value,
            "direction": self.direction.value,
            "strength": self.strength,
            "slope": self.slope,
            "volatility": self.volatility,
            "data_count": len(self.data_points),
            "predictions": [(t.isoformat(), v) for t, v in self.predictions],
            "confidence_interval": self.confidence_interval,
            "seasonal_pattern": self.seasonal_pattern,
            "anomaly_detected": self.anomaly_detected,
        }


@dataclass
class SentimentSegment:
    """User segment with similar sentiment patterns"""

    segment_id: str
    name: str
    size: int
    avg_sentiment: float
    sentiment_variance: float
    dominant_themes: list[str]
    key_characteristics: dict[str, Any] = field(default_factory=dict)
    trend_analysis: SentimentTrend | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "segment_id": self.segment_id,
            "name": self.name,
            "size": self.size,
            "avg_sentiment": self.avg_sentiment,
            "sentiment_variance": self.sentiment_variance,
            "dominant_themes": self.dominant_themes,
            "key_characteristics": self.key_characteristics,
            "trend_analysis": (
                self.trend_analysis.to_dict() if self.trend_analysis else None
            ),
        }


@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""

    widget_id: str
    widget_type: str
    title: str
    data: dict[str, Any]
    config: dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    refresh_interval: int = 300  # seconds

    def to_dict(self) -> dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "widget_type": self.widget_type,
            "title": self.title,
            "data": self.data,
            "config": self.config,
            "last_updated": self.last_updated.isoformat(),
            "refresh_interval": self.refresh_interval,
        }


@dataclass
class SentimentDashboard:
    """Complete sentiment dashboard"""

    dashboard_id: str
    title: str
    time_range: tuple[datetime, datetime]
    widgets: list[DashboardWidget] = field(default_factory=list)
    overall_trends: list[SentimentTrend] = field(default_factory=list)
    segments: list[SentimentSegment] = field(default_factory=list)
    key_insights: list[str] = field(default_factory=list)
    summary_metrics: dict[str, float] = field(default_factory=dict)
    generated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "time_range": [t.isoformat() for t in self.time_range],
            "widgets": [widget.to_dict() for widget in self.widgets],
            "overall_trends": [trend.to_dict() for trend in self.overall_trends],
            "segments": [segment.to_dict() for segment in self.segments],
            "key_insights": self.key_insights,
            "summary_metrics": self.summary_metrics,
            "generated_at": self.generated_at.isoformat(),
        }


class SentimentDashboardService:
    """Comprehensive sentiment dashboard service"""

    def __init__(self):
        self.nlp_service = NLPService()
        self.theme_service = ThemeExtractionService(self.nlp_service)

        # Configuration
        self.config = {
            "min_data_points": 5,
            "anomaly_threshold": 2.0,  # Standard deviations
            "trend_prediction_horizon": 7,  # Days
            "min_segment_size": 10,
            "confidence_level": 0.95,
        }

        # Data storage (in production, this would be database)
        self._sentiment_cache = {}
        self._dashboard_cache = {}
        self._cache_ttl = 1800  # 30 minutes

        logger.info("Sentiment Dashboard Service initialized")

    async def generate_dashboard(
        self,
        texts: list[str],
        timestamps: list[datetime],
        user_ids: list[str] | None = None,
        session_ids: list[str] | None = None,
        time_range: tuple[datetime, datetime] | None = None,
        dashboard_id: str | None = None,
        title: str = "Sentiment Analysis Dashboard",
    ) -> SentimentDashboard:
        """Generate comprehensive sentiment dashboard"""
        try:
            start_time = datetime.utcnow()

            if not time_range:
                time_range = (min(timestamps), max(timestamps))

            if not dashboard_id:
                dashboard_id = f"sentiment_dashboard_{start_time.timestamp()}"

            # Validate inputs
            if len(texts) != len(timestamps):
                raise ValueError("texts and timestamps must have same length")

            # Process sentiment data
            sentiment_data = await self._process_sentiment_data(
                texts, timestamps, user_ids, session_ids
            )

            # Analyze overall trends
            overall_trends = await self._analyze_overall_trends(
                sentiment_data, time_range
            )

            # Perform user segmentation
            segments = await self._perform_user_segmentation(sentiment_data, timestamps)

            # Generate dashboard widgets
            widgets = await self._generate_dashboard_widgets(
                sentiment_data, overall_trends, segments, time_range
            )

            # Generate key insights
            key_insights = await self._generate_key_insights(
                sentiment_data, overall_trends, segments
            )

            # Calculate summary metrics
            summary_metrics = await self._calculate_summary_metrics(sentiment_data)

            processing_time = (datetime.utcnow() - start_time).total_seconds()

            dashboard = SentimentDashboard(
                dashboard_id=dashboard_id,
                title=title,
                time_range=time_range,
                widgets=widgets,
                overall_trends=overall_trends,
                segments=segments,
                key_insights=key_insights,
                summary_metrics=summary_metrics,
                generated_at=datetime.utcnow(),
            )

            # Cache the dashboard
            self._dashboard_cache[dashboard_id] = {
                "dashboard": dashboard,
                "timestamp": datetime.utcnow(),
            }

            logger.info(
                f"Generated sentiment dashboard {dashboard_id} in {processing_time:.2f}s"
            )
            return dashboard

        except Exception as e:
            logger.error(f"Dashboard generation failed: {e!s}")
            # Return empty dashboard with error info
            return SentimentDashboard(
                dashboard_id=dashboard_id or "error_dashboard",
                title="Dashboard Error",
                time_range=(datetime.utcnow(), datetime.utcnow()),
                key_insights=[f"Error: {e!s}"],
            )

    async def _process_sentiment_data(
        self,
        texts: list[str],
        timestamps: list[datetime],
        user_ids: list[str] | None,
        session_ids: list[str] | None,
    ) -> list[SentimentDataPoint]:
        """Process texts and extract sentiment data"""
        try:
            sentiment_data = []

            for i, (text, timestamp) in enumerate(zip(texts, timestamps)):
                # Analyze sentiment
                sentiment_score = await self.nlp_service.analyze_sentiment(text)

                # Extract themes for this text
                themes = await self.theme_service.extract_themes([text], num_themes=3)
                theme_ids = [theme.id for theme in themes]

                data_point = SentimentDataPoint(
                    timestamp=timestamp,
                    sentiment_score=sentiment_score.polarity,
                    sentiment_label=sentiment_score.label,
                    confidence=sentiment_score.confidence,
                    subjectivity=sentiment_score.subjectivity,
                    text_sample=text,
                    user_id=user_ids[i] if user_ids and i < len(user_ids) else None,
                    session_id=(
                        session_ids[i] if session_ids and i < len(session_ids) else None
                    ),
                    theme_ids=theme_ids,
                )

                sentiment_data.append(data_point)

            return sentiment_data

        except Exception as e:
            logger.error(f"Sentiment data processing failed: {e!s}")
            return []

    async def _analyze_overall_trends(
        self,
        sentiment_data: list[SentimentDataPoint],
        time_range: tuple[datetime, datetime],
    ) -> list[SentimentTrend]:
        """Analyze overall sentiment trends"""
        try:
            trends = []

            # Analyze different time periods
            for period in [TrendAnalysisPeriod.DAILY, TrendAnalysisPeriod.WEEKLY]:
                for metric in [SentimentMetric.POLARITY, SentimentMetric.SUBJECTIVITY]:
                    trend = await self._calculate_trend(sentiment_data, metric, period)
                    if trend:
                        trends.append(trend)

            return trends

        except Exception as e:
            logger.error(f"Trend analysis failed: {e!s}")
            return []

    async def _calculate_trend(
        self,
        sentiment_data: list[SentimentDataPoint],
        metric: SentimentMetric,
        period: TrendAnalysisPeriod,
    ) -> SentimentTrend | None:
        """Calculate trend for specific metric and period"""
        try:
            # Group data by time period
            grouped_data = self._group_by_time_period(sentiment_data, period)

            if len(grouped_data) < self.config["min_data_points"]:
                return None

            # Extract values and timestamps
            timestamps = list(grouped_data.keys())
            if metric == SentimentMetric.POLARITY:
                values = [
                    np.mean([dp.sentiment_score for dp in grouped_data[t]])
                    for t in timestamps
                ]
            elif metric == SentimentMetric.SUBJECTIVITY:
                values = [
                    np.mean([dp.subjectivity for dp in grouped_data[t]])
                    for t in timestamps
                ]
            else:
                return None

            # Calculate trend statistics
            slope, strength, direction = self._calculate_linear_trend(
                timestamps, values
            )
            volatility = np.std(values) if len(values) > 1 else 0.0

            # Detect seasonal patterns
            seasonal_pattern = self._detect_seasonality(timestamps, values)

            # Detect anomalies
            anomaly_detected = self._detect_anomalies(values)

            # Generate predictions
            predictions = await self._generate_predictions(timestamps, values, period)

            # Calculate confidence interval
            confidence_interval = self._calculate_confidence_interval(values)

            # Create data points for the trend
            trend_data_points = []
            for timestamp in timestamps:
                if timestamp in grouped_data:
                    for dp in grouped_data[timestamp]:
                        trend_data_points.append(dp)

            return SentimentTrend(
                metric=metric,
                period=period,
                direction=direction,
                strength=strength,
                slope=slope,
                volatility=volatility,
                data_points=trend_data_points,
                predictions=predictions,
                confidence_interval=confidence_interval,
                seasonal_pattern=seasonal_pattern,
                anomaly_detected=anomaly_detected,
            )

        except Exception as e:
            logger.error(f"Trend calculation failed: {e!s}")
            return None

    def _group_by_time_period(
        self, sentiment_data: list[SentimentDataPoint], period: TrendAnalysisPeriod
    ) -> dict[datetime, list[SentimentDataPoint]]:
        """Group sentiment data by time period"""
        grouped = defaultdict(list)

        for dp in sentiment_data:
            if period == TrendAnalysisPeriod.DAILY:
                key = dp.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            elif period == TrendAnalysisPeriod.WEEKLY:
                # Get Monday of the week
                days_since_monday = dp.timestamp.weekday()
                key = (dp.timestamp - timedelta(days=days_since_monday)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
            elif period == TrendAnalysisPeriod.HOURLY:
                key = dp.timestamp.replace(minute=0, second=0, microsecond=0)
            else:
                key = dp.timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

            grouped[key].append(dp)

        return dict(grouped)

    def _calculate_linear_trend(
        self, timestamps: list[datetime], values: list[float]
    ) -> tuple[float, float, TrendDirection]:
        """Calculate linear trend"""
        try:
            if len(values) < 2:
                return 0.0, 0.0, TrendDirection.STABLE

            # Convert timestamps to numeric values
            base_time = timestamps[0]
            x_values = [
                (t - base_time).total_seconds() / 3600 for t in timestamps
            ]  # Hours

            # Simple linear regression
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x_values[i] * values[i] for i in range(n))
            sum_x2 = sum(x * x for x in x_values)

            if n * sum_x2 - sum_x * sum_x == 0:
                return 0.0, 0.0, TrendDirection.STABLE

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)

            # Normalize slope for strength calculation
            avg_value = sum_y / n
            normalized_slope = abs(slope / avg_value) if avg_value != 0 else 0
            strength = min(1.0, normalized_slope * 10)  # Scale to 0-1

            # Determine direction
            if slope > 0.01:
                if strength > 0.7:
                    direction = TrendDirection.STRONGLY_IMPROVING
                else:
                    direction = TrendDirection.IMPROVING
            elif slope < -0.01:
                if strength > 0.7:
                    direction = TrendDirection.STRONGLY_DECLINING
                else:
                    direction = TrendDirection.DECLINING
            # Check for volatility
            elif np.std(values) > 0.3:
                direction = TrendDirection.VOLATILE
            else:
                direction = TrendDirection.STABLE

            return slope, strength, direction

        except Exception as e:
            logger.error(f"Linear trend calculation failed: {e!s}")
            return 0.0, 0.0, TrendDirection.STABLE

    def _detect_seasonality(
        self, timestamps: list[datetime], values: list[float]
    ) -> bool:
        """Detect seasonal patterns in data"""
        try:
            if len(values) < 14:  # Need at least 2 weeks for weekly seasonality
                return False

            # Simple check for weekly patterns
            weekly_averages = defaultdict(list)
            for i, timestamp in enumerate(timestamps):
                if i < len(values):
                    weekly_averages[timestamp.weekday()].append(values[i])

            # Calculate variance between days
            day_averages = [np.mean(vals) for vals in weekly_averages.values() if vals]
            if len(day_averages) < 2:
                return False

            total_variance = np.var(values)
            weekly_variance = np.var(day_averages)

            # If weekly variance is significant portion of total variance, consider it seasonal
            seasonal_ratio = (
                weekly_variance / total_variance if total_variance > 0 else 0
            )

            return seasonal_ratio > 0.3

        except Exception:
            return False

    def _detect_anomalies(self, values: list[float]) -> bool:
        """Detect anomalies in data"""
        try:
            if len(values) < 3:
                return False

            mean_val = np.mean(values)
            std_val = np.std(values)

            # Check for values beyond threshold
            threshold = self.config["anomaly_threshold"]
            anomalies = [v for v in values if abs(v - mean_val) > threshold * std_val]

            return len(anomalies) > 0

        except Exception:
            return False

    async def _generate_predictions(
        self,
        timestamps: list[datetime],
        values: list[float],
        period: TrendAnalysisPeriod,
    ) -> list[tuple[datetime, float]]:
        """Generate simple predictions for future values"""
        try:
            if len(values) < 3:
                return []

            # Use simple linear extrapolation
            base_time = timestamps[0]
            x_values = [
                (t - base_time).total_seconds() / 3600 for t in timestamps
            ]  # Hours

            # Calculate trend
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(values)
            sum_xy = sum(x_values[i] * values[i] for i in range(n))
            sum_x2 = sum(x * x for x in x_values)

            if n * sum_x2 - sum_x * sum_x == 0:
                return []

            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            intercept = (sum_y - slope * sum_x) / n

            # Generate predictions
            predictions = []
            last_timestamp = timestamps[-1]
            horizon_hours = self.config["trend_prediction_horizon"] * 24

            for hours_ahead in range(
                1, min(24, self.config["trend_prediction_horizon"])
            ):
                future_x = x_values[-1] + hours_ahead
                if period == TrendAnalysisPeriod.DAILY:
                    future_time = last_timestamp + timedelta(hours=hours_ahead * 24)
                elif period == TrendAnalysisPeriod.WEEKLY:
                    future_time = last_timestamp + timedelta(weeks=hours_ahead)
                else:
                    future_time = last_timestamp + timedelta(hours=hours_ahead)

                predicted_value = slope * future_x + intercept
                predictions.append((future_time, predicted_value))

            return predictions

        except Exception as e:
            logger.error(f"Prediction generation failed: {e!s}")
            return []

    def _calculate_confidence_interval(
        self, values: list[float]
    ) -> tuple[float, float]:
        """Calculate confidence interval for values"""
        try:
            if len(values) < 2:
                return (0.0, 0.0)

            mean_val = np.mean(values)
            std_val = np.std(values)

            # 95% confidence interval
            margin = 1.96 * std_val / np.sqrt(len(values))

            return (mean_val - margin, mean_val + margin)

        except Exception:
            return (0.0, 0.0)

    async def _perform_user_segmentation(
        self, sentiment_data: list[SentimentDataPoint], timestamps: list[datetime]
    ) -> list[SentimentSegment]:
        """Perform user segmentation based on sentiment patterns"""
        try:
            # Group by user
            user_data = defaultdict(list)
            for dp in sentiment_data:
                if dp.user_id:
                    user_data[dp.user_id].append(dp)

            if len(user_data) < self.config["min_segment_size"]:
                return []

            # Calculate features for each user
            user_features = {}
            for user_id, user_dps in user_data.items():
                if len(user_dps) < 3:  # Need sufficient data per user
                    continue

                sentiments = [dp.sentiment_score for dp in user_dps]
                subjectivities = [dp.subjectivity for dp in user_dps]

                features = {
                    "avg_sentiment": np.mean(sentiments),
                    "sentiment_variance": np.var(sentiments),
                    "avg_subjectivity": np.mean(subjectivities),
                    "data_points": len(user_dps),
                    "sentiment_range": max(sentiments) - min(sentiments),
                }

                user_features[user_id] = features

            if len(user_features) < self.config["min_segment_size"]:
                return []

            # Simple clustering based on sentiment patterns
            segments = self._cluster_users(user_features)

            # Analyze trends for each segment
            for segment in segments:
                segment_dps = []
                for user_id in [
                    u
                    for u in user_features
                    if any(u in s.get("users", []) for s in segments)
                ]:
                    if user_id in user_data:
                        segment_dps.extend(user_data[user_id])

                if segment_dps:
                    segment_trend = await self._calculate_trend(
                        segment_dps, SentimentMetric.POLARITY, TrendAnalysisPeriod.DAILY
                    )
                    segment["trend_analysis"] = segment_trend

            return segments

        except Exception as e:
            logger.error(f"User segmentation failed: {e!s}")
            return []

    def _cluster_users(
        self, user_features: dict[str, dict[str, float]]
    ) -> list[SentimentSegment]:
        """Simple user clustering based on sentiment features"""
        try:
            # Extract feature matrix
            users = list(user_features.keys())
            features = []
            for user in users:
                f = user_features[user]
                features.append(
                    [f["avg_sentiment"], f["sentiment_variance"], f["avg_subjectivity"]]
                )

            # Normalize features
            scaler = StandardScaler()
            try:
                normalized_features = scaler.fit_transform(features).tolist()
            except Exception as e:
                normalized_features = features

            # Simple k-means-like clustering
            n_clusters = min(4, len(users) // self.config["min_segment_size"])
            if n_clusters < 2:
                return []

            # Initialize cluster centers
            centers = normalized_features[:n_clusters]

            # Assign users to clusters
            clusters = [[] for _ in range(n_clusters)]
            for i, feature in enumerate(normalized_features):
                distances = [
                    np.linalg.norm(np.array(feature) - np.array(center))
                    for center in centers
                ]
                closest_cluster = np.argmin(distances)
                clusters[closest_cluster].append(users[i])

            # Create segment objects
            segments = []
            for i, cluster_users in enumerate(clusters):
                if len(cluster_users) >= self.config["min_segment_size"]:
                    # Calculate cluster statistics
                    cluster_sentiments = [
                        user_features[u]["avg_sentiment"] for u in cluster_users
                    ]
                    cluster_variances = [
                        user_features[u]["sentiment_variance"] for u in cluster_users
                    ]

                    segment = SentimentSegment(
                        segment_id=f"segment_{i}",
                        name=f"Sentiment Segment {i + 1}",
                        size=len(cluster_users),
                        avg_sentiment=np.mean(cluster_sentiments),
                        sentiment_variance=np.mean(cluster_variances),
                        dominant_themes=[],  # Would need theme analysis
                        key_characteristics={
                            "users": cluster_users,
                            "avg_data_points": np.mean(
                                [user_features[u]["data_points"] for u in cluster_users]
                            ),
                        },
                    )
                    segments.append(segment)

            return segments

        except Exception as e:
            logger.error(f"User clustering failed: {e!s}")
            return []

    async def _generate_dashboard_widgets(
        self,
        sentiment_data: list[SentimentDataPoint],
        trends: list[SentimentTrend],
        segments: list[SentimentSegment],
        time_range: tuple[datetime, datetime],
    ) -> list[DashboardWidget]:
        """Generate dashboard widgets"""
        try:
            widgets = []

            # Sentiment trend widget
            trend_widget = await self._create_trend_widget(trends, time_range)
            widgets.append(trend_widget)

            # Sentiment distribution widget
            distribution_widget = await self._create_distribution_widget(sentiment_data)
            widgets.append(distribution_widget)

            # Sentiment timeline widget
            timeline_widget = await self._create_timeline_widget(
                sentiment_data, time_range
            )
            widgets.append(timeline_widget)

            # User segments widget
            segments_widget = await self._create_segments_widget(segments)
            widgets.append(segments_widget)

            # Key metrics widget
            metrics_widget = await self._create_metrics_widget(sentiment_data, trends)
            widgets.append(metrics_widget)

            # Sentiment volatility widget
            volatility_widget = await self._create_volatility_widget(trends)
            widgets.append(volatility_widget)

            return widgets

        except Exception as e:
            logger.error(f"Widget generation failed: {e!s}")
            return []

    async def _create_trend_widget(
        self, trends: list[SentimentTrend], time_range: tuple[datetime, datetime]
    ) -> DashboardWidget:
        """Create sentiment trend widget"""
        try:
            # Prepare trend data for visualization
            trend_data = []
            for trend in trends:
                if (
                    trend.metric == SentimentMetric.POLARITY
                    and trend.period == TrendAnalysisPeriod.DAILY
                ):
                    timestamps = []
                    values = []

                    # Aggregate data points by day
                    daily_data = defaultdict(list)
                    for dp in trend.data_points:
                        day_key = dp.timestamp.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )
                        daily_data[day_key].append(dp.sentiment_score)

                    for day in sorted(daily_data.keys()):
                        timestamps.append(day.isoformat())
                        values.append(np.mean(daily_data[day]))

                    trend_data.append(
                        {
                            "timestamps": timestamps,
                            "values": values,
                            "predictions": [
                                (t.isoformat(), v) for t, v in trend.predictions
                            ],
                            "direction": trend.direction.value,
                            "strength": trend.strength,
                            "confidence_interval": trend.confidence_interval,
                        }
                    )
                    break

            return DashboardWidget(
                widget_id="sentiment_trend",
                widget_type="line_chart",
                title="Sentiment Trend Over Time",
                data={
                    "trends": trend_data,
                    "time_range": [t.isoformat() for t in time_range],
                },
                config={
                    "xAxis": "Time",
                    "yAxis": "Sentiment Score",
                    "showPrediction": True,
                    "showConfidenceInterval": True,
                },
            )

        except Exception as e:
            logger.error(f"Trend widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="sentiment_trend",
                widget_type="error",
                title="Sentiment Trend Error",
                data={"error": str(e)},
            )

    async def _create_distribution_widget(
        self, sentiment_data: list[SentimentDataPoint]
    ) -> DashboardWidget:
        """Create sentiment distribution widget"""
        try:
            # Count sentiment labels
            label_counts = Counter(dp.sentiment_label.value for dp in sentiment_data)
            total_count = len(sentiment_data)

            # Calculate percentages
            distribution = []
            for label in [
                "very_positive",
                "positive",
                "neutral",
                "negative",
                "very_negative",
            ]:
                count = label_counts.get(label, 0)
                percentage = (count / total_count * 100) if total_count > 0 else 0
                distribution.append(
                    {
                        "label": label.replace("_", " ").title(),
                        "count": count,
                        "percentage": percentage,
                    }
                )

            return DashboardWidget(
                widget_id="sentiment_distribution",
                widget_type="pie_chart",
                title="Sentiment Distribution",
                data={"distribution": distribution},
                config={"showPercentage": True, "showCount": True},
            )

        except Exception as e:
            logger.error(f"Distribution widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="sentiment_distribution",
                widget_type="error",
                title="Sentiment Distribution Error",
                data={"error": str(e)},
            )

    async def _create_timeline_widget(
        self,
        sentiment_data: list[SentimentDataPoint],
        time_range: tuple[datetime, datetime],
    ) -> DashboardWidget:
        """Create sentiment timeline widget"""
        try:
            # Create hourly sentiment timeline
            timeline_data = defaultdict(list)

            for dp in sentiment_data:
                hour_key = dp.timestamp.replace(minute=0, second=0, microsecond=0)
                timeline_data[hour_key].append(dp.sentiment_score)

            # Prepare data for visualization
            timestamps = []
            values = []
            counts = []

            for hour in sorted(timeline_data.keys()):
                timestamps.append(hour.isoformat())
                hour_scores = timeline_data[hour]
                values.append(np.mean(hour_scores))
                counts.append(len(hour_scores))

            return DashboardWidget(
                widget_id="sentiment_timeline",
                widget_type="timeline",
                title="Sentiment Timeline",
                data={
                    "timestamps": timestamps,
                    "values": values,
                    "counts": counts,
                    "time_range": [t.isoformat() for t in time_range],
                },
                config={"showVolume": True, "smoothLine": True},
            )

        except Exception as e:
            logger.error(f"Timeline widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="sentiment_timeline",
                widget_type="error",
                title="Sentiment Timeline Error",
                data={"error": str(e)},
            )

    async def _create_segments_widget(
        self, segments: list[SentimentSegment]
    ) -> DashboardWidget:
        """Create user segments widget"""
        try:
            segments_data = []
            for segment in segments:
                segments_data.append(
                    {
                        "segment_id": segment.segment_id,
                        "name": segment.name,
                        "size": segment.size,
                        "avg_sentiment": segment.avg_sentiment,
                        "sentiment_variance": segment.sentiment_variance,
                        "trend_direction": (
                            segment.trend_analysis.direction.value
                            if segment.trend_analysis
                            else "unknown"
                        ),
                    }
                )

            return DashboardWidget(
                widget_id="user_segments",
                widget_type="bar_chart",
                title="User Sentiment Segments",
                data={"segments": segments_data},
                config={
                    "xAxis": "Segment",
                    "yAxis": "Average Sentiment",
                    "showSize": True,
                },
            )

        except Exception as e:
            logger.error(f"Segments widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="user_segments",
                widget_type="error",
                title="User Segments Error",
                data={"error": str(e)},
            )

    async def _create_metrics_widget(
        self, sentiment_data: list[SentimentDataPoint], trends: list[SentimentTrend]
    ) -> DashboardWidget:
        """Create key metrics widget"""
        try:
            # Calculate metrics
            total_entries = len(sentiment_data)
            avg_sentiment = (
                np.mean([dp.sentiment_score for dp in sentiment_data])
                if sentiment_data
                else 0
            )
            avg_confidence = (
                np.mean([dp.confidence for dp in sentiment_data])
                if sentiment_data
                else 0
            )
            avg_subjectivity = (
                np.mean([dp.subjectivity for dp in sentiment_data])
                if sentiment_data
                else 0
            )

            # Find dominant trend
            dominant_trend = None
            for trend in trends:
                if (
                    trend.metric == SentimentMetric.POLARITY
                    and trend.period == TrendAnalysisPeriod.DAILY
                ):
                    dominant_trend = trend
                    break

            metrics_data = {
                "total_entries": total_entries,
                "avg_sentiment": round(avg_sentiment, 3),
                "avg_confidence": round(avg_confidence, 3),
                "avg_subjectivity": round(avg_subjectivity, 3),
                "dominant_trend": (
                    dominant_trend.direction.value if dominant_trend else "stable"
                ),
                "trend_strength": (
                    round(dominant_trend.strength, 3) if dominant_trend else 0
                ),
                "anomaly_detected": any(t.anomaly_detected for t in trends),
            }

            return DashboardWidget(
                widget_id="key_metrics",
                widget_type="metrics",
                title="Key Sentiment Metrics",
                data=metrics_data,
                config={"showTrend": True, "showAnomalies": True},
            )

        except Exception as e:
            logger.error(f"Metrics widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="key_metrics",
                widget_type="error",
                title="Key Metrics Error",
                data={"error": str(e)},
            )

    async def _create_volatility_widget(
        self, trends: list[SentimentTrend]
    ) -> DashboardWidget:
        """Create sentiment volatility widget"""
        try:
            volatility_data = []
            for trend in trends:
                if trend.metric == SentimentMetric.POLARITY:
                    volatility_data.append(
                        {
                            "period": trend.period.value,
                            "volatility": round(trend.volatility, 3),
                            "direction": trend.direction.value,
                            "anomaly_detected": trend.anomaly_detected,
                        }
                    )

            return DashboardWidget(
                widget_id="sentiment_volatility",
                widget_type="gauge_chart",
                title="Sentiment Volatility",
                data={"volatility": volatility_data},
                config={"minValue": 0, "maxValue": 1, "thresholds": [0.1, 0.3, 0.5]},
            )

        except Exception as e:
            logger.error(f"Volatility widget creation failed: {e!s}")
            return DashboardWidget(
                widget_id="sentiment_volatility",
                widget_type="error",
                title="Sentiment Volatility Error",
                data={"error": str(e)},
            )

    async def _generate_key_insights(
        self,
        sentiment_data: list[SentimentDataPoint],
        trends: list[SentimentTrend],
        segments: list[SentimentSegment],
    ) -> list[str]:
        """Generate key insights from sentiment analysis"""
        try:
            insights = []

            if not sentiment_data:
                return ["No sentiment data available for analysis"]

            # Overall sentiment insight
            avg_sentiment = np.mean([dp.sentiment_score for dp in sentiment_data])
            if avg_sentiment > 0.3:
                insights.append(f"Overall sentiment is positive ({avg_sentiment:.2f})")
            elif avg_sentiment < -0.3:
                insights.append(f"Overall sentiment is negative ({avg_sentiment:.2f})")
            else:
                insights.append(f"Overall sentiment is neutral ({avg_sentiment:.2f})")

            # Trend insights
            for trend in trends:
                if (
                    trend.metric == SentimentMetric.POLARITY
                    and trend.period == TrendAnalysisPeriod.DAILY
                ):
                    if trend.direction in [
                        TrendDirection.IMPROVING,
                        TrendDirection.STRONGLY_IMPROVING,
                    ]:
                        insights.append(
                            f"Sentiment is improving over time (strength: {trend.strength:.2f})"
                        )
                    elif trend.direction in [
                        TrendDirection.DECLINING,
                        TrendDirection.STRONGLY_DECLINING,
                    ]:
                        insights.append(
                            f"Sentiment is declining over time (strength: {trend.strength:.2f})"
                        )

                    if trend.seasonal_pattern:
                        insights.append("Seasonal patterns detected in sentiment data")

                    if trend.anomaly_detected:
                        insights.append("Anomalies detected in sentiment patterns")

            # Volatility insight
            volatilities = [
                t.volatility for t in trends if t.metric == SentimentMetric.POLARITY
            ]
            if volatilities:
                avg_volatility = np.mean(volatilities)
                if avg_volatility > 0.3:
                    insights.append(
                        f"High sentiment volatility detected ({avg_volatility:.2f})"
                    )
                elif avg_volatility < 0.1:
                    insights.append(
                        f"Low sentiment volatility indicates stable patterns ({avg_volatility:.2f})"
                    )

            # Segment insights
            if len(segments) > 1:
                insights.append(
                    f"{len(segments)} distinct user sentiment segments identified"
                )

                # Find most positive and most negative segments
                if segments:
                    most_positive = max(segments, key=lambda s: s.avg_sentiment)
                    most_negative = min(segments, key=lambda s: s.avg_sentiment)

                    insights.append(
                        f"Most positive segment: {most_positive.name} (avg: {most_positive.avg_sentiment:.2f})"
                    )
                    insights.append(
                        f"Most negative segment: {most_negative.name} (avg: {most_negative.avg_sentiment:.2f})"
                    )

            # Confidence insight
            avg_confidence = np.mean([dp.confidence for dp in sentiment_data])
            if avg_confidence < 0.6:
                insights.append(
                    f"Low confidence in sentiment analysis ({avg_confidence:.2f}) - consider more data"
                )
            elif avg_confidence > 0.8:
                insights.append(
                    f"High confidence in sentiment analysis ({avg_confidence:.2f})"
                )

            return insights[:10]  # Limit to top 10 insights

        except Exception as e:
            logger.error(f"Insight generation failed: {e!s}")
            return [f"Error generating insights: {e!s}"]

    async def _calculate_summary_metrics(
        self, sentiment_data: list[SentimentDataPoint]
    ) -> dict[str, float]:
        """Calculate summary metrics"""
        try:
            if not sentiment_data:
                return {}

            sentiments = [dp.sentiment_score for dp in sentiment_data]
            confidences = [dp.confidence for dp in sentiment_data]
            subjectivities = [dp.subjectivity for dp in sentiment_data]

            return {
                "total_entries": len(sentiment_data),
                "avg_sentiment": float(np.mean(sentiments)),
                "sentiment_std": float(np.std(sentiments)),
                "min_sentiment": float(np.min(sentiments)),
                "max_sentiment": float(np.max(sentiments)),
                "avg_confidence": float(np.mean(confidences)),
                "avg_subjectivity": float(np.mean(subjectivities)),
                "positive_ratio": float(
                    sum(1 for s in sentiments if s > 0.1) / len(sentiments)
                ),
                "negative_ratio": float(
                    sum(1 for s in sentiments if s < -0.1) / len(sentiments)
                ),
                "neutral_ratio": float(
                    sum(1 for s in sentiments if -0.1 <= s <= 0.1) / len(sentiments)
                ),
            }

        except Exception as e:
            logger.error(f"Summary metrics calculation failed: {e!s}")
            return {}

    def export_dashboard_json(self, dashboard: SentimentDashboard) -> str:
        """Export dashboard to JSON format"""
        try:
            return json.dumps(dashboard.to_dict(), indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Dashboard JSON export failed: {e!s}")
            return "{}"

    def export_widget_data(self, widget: DashboardWidget) -> dict[str, Any]:
        """Export individual widget data"""
        return widget.to_dict()


# Import numpy for statistical calculations
try:
    import numpy as np
except ImportError:
    # Fallback if numpy not available
    import statistics as np


# Export the main service class
__all__ = [
    "DashboardWidget",
    "SentimentDashboard",
    "SentimentDashboardService",
    "SentimentDataPoint",
    "SentimentMetric",
    "SentimentSegment",
    "SentimentTrend",
    "TrendAnalysisPeriod",
    "TrendDirection",
]
