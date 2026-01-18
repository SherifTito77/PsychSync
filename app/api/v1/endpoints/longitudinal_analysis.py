"""
Longitudinal Analysis API Endpoints
REST API endpoints for longitudinal behavioral analysis, change detection, and trend analysis.
"""

from typing import List, Dict, Any, Optional

from app.core.rate_limiter_unified import rate_limit, RateLimitStrategy
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_active_user
# from app.services.longitudinal_analysis import LongitudinalAnalyzer, MetricType
# from app.services.change_detection import AdvancedChangeDetector, ChangeDetectionMode
# from app.api.dependencies import get_current_active_user, require_permission
from app.db.models.user import User

router = APIRouter(prefix="/longitudinal", tags=["longitudinal-analysis"])

# Pydantic models for request/response
class TimeSeriesAggregationRequest(BaseModel):
    """Request model for time series data aggregation."""
    user_id: str = Field(..., description="User ID to aggregate data for")
    metric_name: str = Field(..., description="Metric name to aggregate")
    start_time: datetime = Field(..., description="Start time for aggregation")
    end_time: datetime = Field(..., description="End time for aggregation")
    bucket_size: str = Field("day", description="Bucket size (hour, day, week, month)")

class ChangeDetectionRequest(BaseModel):
    """Request model for change detection."""
    user_id: str = Field(..., description="User ID to analyze")
    metric_name: str = Field(..., description="Metric name to analyze")
    detection_mode: str = Field("streaming", description="Detection mode (streaming, batch, hybrid)")
    algorithms: Optional[List[str]] = Field(None, description="Algorithms to use")
    sensitivity: float = Field(0.05, description="Detection sensitivity")
    include_forecasts: bool = Field(True, description="Include forecast data")

class TrendAnalysisRequest(BaseModel):
    """Request model for trend analysis."""
    user_id: str = Field(..., description="User ID to analyze")
    metric_name: str = Field(..., description="Metric name to analyze")
    start_time: datetime = Field(..., description="Start time for analysis")
    end_time: datetime = Field(..., description="End time for analysis")
    include_seasonal: bool = Field(True, description="Include seasonal analysis")
    confidence_level: float = Field(0.95, description="Confidence level for analysis")

class BaselineCalculationRequest(BaseModel):
    """Request model for baseline calculation."""
    user_id: str = Field(..., description="User ID to calculate baseline for")
    metric_name: str = Field(..., description="Metric name to calculate baseline for")
    baseline_type: str = Field("personal", description="Baseline type")
    baseline_period_days: int = Field(30, description="Period for baseline calculation in days")

class UserProgressionRequest(BaseModel):
    """Request model for user progression analysis."""
    user_id: str = Field(..., description="User ID to analyze")
    metrics: List[str] = Field(..., description="List of metrics to analyze")
    time_range_days: int = Field(90, description="Time range for analysis in days")
    include_change_points: bool = Field(True, description="Include change point detection")
    include_baselines: bool = Field(True, description="Include baseline comparison")

class ComparisonRequest(BaseModel):
    """Request model for longitudinal comparison."""
    user_ids: List[str] = Field(..., description="User IDs to compare")
    metrics: List[str] = Field(..., description="Metrics to compare")
    time_range_days: int = Field(90, description="Time range for comparison")
    include_change_points: bool = Field(True, description="Include change points in comparison")
    include_trends: bool = Field(True, description="Include trend analysis")

class TimeSeriesAggregationResponse(BaseModel):
    """Response model for time series aggregation."""
    user_id: str
    metric_name: str
    bucket_size: str
    data_points: List[Dict[str, Any]]
    total_points: int
    date_range: Dict[str, str]
    aggregation_timestamp: str

class ChangeDetectionResponse(BaseModel):
    """Response model for change detection results."""
    user_id: str
    metric_name: str
    detection_mode: str
    change_points: List[Dict[str, Any]]
    algorithm_performance: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    detection_timestamp: str

class TrendAnalysisResponse(BaseModel):
    """Response model for trend analysis."""
    user_id: str
    metric_name: str
    analysis_period: Dict[str, Any]
    trend_direction: str
    trend_slope: float
    trend_intercept: float
    r_squared: float
    p_value: float
    seasonal_component: bool
    seasonal_period: Optional[int]
    seasonal_strength: Optional[float]
    confidence_level: float
    forecast: Optional[Dict[str, Any]]
    statistical_tests: Dict[str, Any]
    analysis_timestamp: str

class BaselineCalculationResponse(BaseModel):
    """Response model for baseline calculation."""
    baseline_id: str
    user_id: str
    metric_name: str
    baseline_type: str
    baseline_period: Dict[str, str]
    statistics: Dict[str, Any]
    confidence_level: float
    margin_of_error: float
    created_at: str

class UserProgressionResponse(BaseModel):
    """Response model for user progression analysis."""
    user_id: str
    analysis_period: Dict[str, Any]
    metrics_analysis: Dict[str, Dict[str, Any]]
    overall_insights: List[Dict[str, Any]]
    recommendations: List[str]
    risk_indicators: List[Dict[str, Any]]
    analysis_timestamp: str


@rate_limit(limit=100, window=60, strategy=RateLimitStrategy.SLIDING_WINDOW)
@router.post("/aggregate-time-series", response_model=TimeSeriesAggregationResponse)
async def aggregate_time_series_data(
    request: TimeSeriesAggregationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregate behavioral data into time series buckets.

    - **user_id**: User ID to aggregate data for
    - **metric_name**: Metric name to aggregate
    - **start_time**: Start time for aggregation
    - **end_time**: End time for aggregation
    - **bucket_size**: Size of time buckets (hour, day, week, month)

    Returns aggregated time series data with metadata.
    """
    try:
        # Check permissions
        if request.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to aggregate data for this user"
            )

        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Aggregate time series data
        time_series_data = await analyzer.aggregate_time_series_data(
            user_id=request.user_id,
            metric_name=request.metric_name,
            start_time=request.start_time,
            end_time=request.end_time,
            bucket_size=request.bucket_size
        )

        # Convert to response format
        response_data = {
            'user_id': request.user_id,
            'metric_name': request.metric_name,
            'bucket_size': request.bucket_size,
            'data_points': [
                {
                    'timestamp': point.timestamp.isoformat(),
                    'value': float(point.value),
                    'context': point.context
                }
                for point in time_series_data
            ],
            'total_points': len(time_series_data),
            'date_range': {
                'start': request.start_time.isoformat(),
                'end': request.end_time.isoformat()
            },
            'aggregation_timestamp': datetime.utcnow().isoformat()
        }

        return TimeSeriesAggregationResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error aggregating time series data: {str(e)}"
        ) from e
@router.post("/detect-changes", response_model=ChangeDetectionResponse)
async def detect_behavioral_changes(
    request: ChangeDetectionRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect behavioral changes using advanced algorithms.

    - **user_id**: User ID to analyze
    - **metric_name**: Metric name to analyze
    - **detection_mode**: Detection mode (streaming, batch, hybrid)
    - **algorithms**: Algorithms to use for detection
    - **sensitivity**: Detection sensitivity level
    - **include_forecasts**: Whether to include forecast data

    Returns detected change points with analysis results.
    """
    try:
        # Check permissions
        if request.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this user's data"
            )

        # Initialize change detector
        change_detector = AdvancedChangeDetector(db)

        # Get time series data for analysis
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=90)

        # TODO(human): Get actual data from database
        # For now, use mock data
        time_series_data = []
        current_value = 50

        for i in range(90):
            timestamp = start_time + timedelta(days=i)
            # Generate realistic data with potential changes
            if (i == 30 or i == 60) and i % 10 == 0:
                current_value += (hash(str(i)) % 20 - 10)

            current_value += (hash(str(i)) % 7 - 3) * 0.5
            current_value = max(10, min(100, current_value))

            time_series_data.append((timestamp, current_value))

        # Detect changes
        if request.detection_mode == "streaming":
            # For streaming, process each point individually
            all_alerts = []
            for timestamp, value in time_series_data:
                alerts = await change_detector.detect_changes_streaming(
                    user_id=request.user_id,
                    metric_name=request.metric_name,
                    new_value=value,
                    timestamp=timestamp,
                    algorithms=[],
                    context={'sensitivity': request.sensitivity}
                )
                all_alerts.extend(alerts)
            change_points = all_alerts
        else:
            # Batch processing
            algorithms = request.algorithms or ['cusum', 'ewma', 'ensemble']
            algorithm_mapping = {
                'cusum': 'cusum',
                'ewma': 'ewma',
                'page_hinkley': 'page_hinkley',
                'bayesian': 'bayesian',
                'change_finder': 'change_finder',
                'ensemble': 'ensemble_stream'
            }

            mapped_algorithms = []
            for algo in algorithms:
                if algo in algorithm_mapping:
                    mapped_algorithms.append(algorithm_mapping[algo])

            # Convert DetectionMethod string to enum
            from app.services.change_detection import DetectionMethod
            detection_algorithms = []
            for algo in mapped_algorithms:
                try:
                    detection_algorithms.append(DetectionMethod(algo))
                except ValueError:
                    logger.warning(f"Unknown algorithm: {algo}")

            change_points = await change_detector.detect_changes_batch(
                user_id=request.user_id,
                metric_name=request.metric_name,
                data_points=time_series_data,
                algorithms=detection_algorithms
            )

        # Convert to response format
        response_data = {
            'user_id': request.user_id,
            'metric_name': request.metric_name,
            'detection_mode': request.detection_mode,
            'change_points': [
                {
                    'change_point_id': cp.change_point_id,
                    'user_id': cp.user_id,
                    'metric_name': cp.metric_name,
                    'algorithm': cp.algorithm.value,
                    'change_type': cp.change_type.value,
                    'severity': cp.severity.value,
                    'detected_at': cp.detected_at.isoformat(),
                    'baseline_value': cp.baseline_value,
                    'current_value': cp.current_value,
                    'change_magnitude': cp.change_magnitude,
                    'confidence': cp.confidence,
                    'statistical_significance': cp.statistical_significance,
                    'description': cp.description,
                    'recommended_actions': cp.recommended_actions,
                    'context': cp.context
                }
                for cp in change_points
            ],
            'algorithm_performance': [
                {
                    'algorithm': algo,
                    'true_positives': 5,  # Mock data
                    'false_positives': 1,
                    'precision': 0.83,
                    'recall': 0.71,
                    'f1_score': 0.77
                }
                for algo in (request.algorithms or ['cusum', 'ewma'])
            ],
            'statistics': {
                'total_data_points': len(time_series_data),
                'change_points_detected': len(change_points),
                'detection_sensitivity': request.sensitivity,
                'processing_time_ms': 150  # Mock processing time
            },
            'detection_timestamp': datetime.utcnow().isoformat()
        }

        return ChangeDetectionResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error detecting changes: {str(e)}"
        ) from e

@router.post("/analyze-trends", response_model=TrendAnalysisResponse)
async def analyze_trends(
    request: TrendAnalysisRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze trends in time series data.

    - **user_id**: User ID to analyze
    - **metric_name**: Metric name to analyze
    - **start_time**: Start time for analysis
    - **end_time**: End time for analysis
    - **include_seasonal**: Whether to include seasonal analysis
    - **confidence_level**: Confidence level for statistical tests

    Returns comprehensive trend analysis results.
    """
    try:
        # Check permissions
        if request.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this user's trends"
            )

        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Get time series data for analysis
        # TODO(human): Get actual data from database
        time_series_data = []
        current_value = 45

        for i in range(request.end_time.day - request.start_time.day):
            timestamp = request.start_time + timedelta(days=i)

            # Generate trend data with some seasonality
            base_value = 45 + (i * 0.3)  # Upward trend
            seasonal_value = 8 * np.sin(2 * np.pi * i / 7)  # Weekly seasonality
            noise = (hash(str(i)) % 11 - 5) * 2  # Random noise

            value = max(10, base_value + seasonal_value + noise)
            current_value = value

            time_series_data.append({
                'timestamp': timestamp,
                'value': value,
                'metric_name': request.metric_name,
                'user_id': request.user_id,
                'bucket_size': 'day'
            })

        # Convert to TimeSeriesPoint objects
        from app.services.longitudinal_analysis import TimeSeriesPoint
        time_series_points = [
            TimeSeriesPoint(
                timestamp=point['timestamp'],
                value=point['value'],
                metric_name=point['metric_name'],
                user_id=point['user_id'],
                bucket_size='day'
            )
            for point in time_series_data
        ]

        # Perform trend analysis
        trend_analysis = await analyzer.analyze_trends(
            user_id=request.user_id,
            metric_name=request.metric_name,
            time_series_data=time_series_points
        )

        if not trend_analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No trend analysis results available"
            )

        # Convert to response format
        response_data = {
            'user_id': trend_analysis.user_id,
            'metric_name': trend_analysis.metric_name,
            'analysis_period': {
                'start': trend_analysis.analysis_period_start.isoformat(),
                'end': trend_analysis.analysis_period_end.isoformat(),
                'days': (trend_analysis.analysis_period_end - trend_analysis.analysis_period_start).days
            },
            'trend_direction': trend_analysis.trend_direction.value,
            'trend_slope': trend_analysis.trend_slope,
            'trend_intercept': trend_analysis.trend_intercept,
            'r_squared': trend_analysis.r_squared,
            'p_value': trend_analysis.p_value,
            'seasonal_component': trend_analysis.seasonal_component,
            'seasonal_period': trend_analysis.seasonal_period,
            'seasonal_strength': trend_analysis.seasonal_strength,
            'confidence_level': trend_analysis.confidence_level,
            'forecast': {
                'next_period': trend_analysis.forecast_next_period,
                'confidence_lower': trend_analysis.forecast_confidence_lower,
                'confidence_upper': trend_analysis.forecast_confidence_upper,
                'forecast_horizon_days': 7
            } if trend_analysis.forecast_next_period else None,
            'statistical_tests': {
                'stationarity_test': 'ADF Test',
                'stationarity_p_value': 0.01,  # Mock value
                'trend_test': 'Mann-Kendall',
                'trend_p_value': 0.05,  # Mock value
                'seasonal_test': 'Seasonal Decomposition' if trend_analysis.seasonal_component else None,
                'seasonal_p_value': 0.03 if trend_analysis.seasonal_component else None
            },
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

        return TrendAnalysisResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing trends: {str(e)}"
        ) from e
@router.post("/calculate-baseline", response_model=BaselineCalculationResponse)
async def calculate_baseline(
    request: BaselineCalculationRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Calculate behavioral baseline for comparison.

    - **user_id**: User ID to calculate baseline for
    - **metric_name**: Metric name to calculate baseline for
    - **baseline_type**: Type of baseline (personal, peer_group, organizational)
    - **baseline_period_days**: Period for baseline calculation

    Returns calculated baseline with statistics.
    """
    try:
        # Check permissions
        if request.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to calculate baseline for this user"
            )

        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Calculate baseline
        baseline = await analyzer.calculate_baseline(
            user_id=request.user_id,
            metric_name=request.metric_name,
            baseline_type=request.baseline_type,
            baseline_period_days=request.baseline_period_days
        )

        if not baseline:
            raise HTTPException(
                status=status.HTTP_404_NOT_FOUND,
                detail="Insufficient data for baseline calculation"
            )

        # Convert to response format
        response_data = {
            'baseline_id': baseline.id,
            'user_id': baseline.user_id,
            'metric_name': baseline.metric_name,
            'baseline_type': baseline.baseline_type,
            'baseline_period': {
                'start': baseline.baseline_period_start.isoformat(),
                'end': baseline.baseline_period_end.isoformat(),
                'days': (baseline.baseline_period_end - baseline.baseline_period_start).days
            },
            'statistics': {
                'mean_value': baseline.mean_value,
                'median_value': baseline.median_value,
                'std_deviation': baseline.std_deviation,
                'min_value': baseline.min_value,
                'max_value': baseline.max_value,
                'percentile_25': baseline.percentile_25,
                'percentile_75': baseline.percentile_75,
                'sample_size': baseline.sample_size
            },
            'confidence_level': baseline.confidence_level,
            'margin_of_error': baseline.margin_of_error,
            'created_at': datetime.utcnow().isoformat()
        }

        return BaselineCalculationResponse(**response_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating baseline: {str(e)}"
        ) from e
@router.post("/analyze-user-progression", response_model=UserProgressionResponse)
async def analyze_user_progression(
    request: UserProgressionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Analyze comprehensive user progression over time.

    - **user_id**: User ID to analyze
    - **metrics**: List of metrics to analyze
    - **time_range_days**: Time range for analysis in days
    - **include_change_points**: Whether to include change point detection
    - **include_baselines**: Whether to include baseline comparison

    Returns comprehensive progression analysis with insights and recommendations.
    """
    try:
        # Check permissions
        if request.user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to analyze this user's progression"
            )

        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Perform comprehensive analysis
        progression_analysis = await analyzer.analyze_user_progression(
            user_id=request.user_id,
            metrics=request.metrics,
            time_range_days=request.time_range_days
        )

        # Convert to response format
        response_data = {
            'user_id': progression_analysis['user_id'],
            'analysis_period': progression_analysis['analysis_period'],
            'metrics_analysis': progression_analysis['metrics_analysis'],
            'overall_insights': progression_analysis['overall_insights'],
            'recommendations': progression_analysis['recommendations'],
            'risk_indicators': progression_analysis['risk_indicators'],
            'analysis_timestamp': datetime.utcnow().isoformat()
        }

        return UserProgressionResponse(**response_data)

    except Exception as e:
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing user progression: {str(e)}"
        ) from e
@router.post("/compare-users", response_model=Dict[str, Any])
async def compare_longitudinal_data(
    request: ComparisonRequest,
    # current_user: User = Depends(require_permission("admin")),  # TODO: Implement permissions
    db: AsyncSession = Depends(get_db)
):
    """
    Compare longitudinal data across multiple users.

    - **user_ids**: User IDs to compare
    - **metrics**: Metrics to compare
    - **time_range_days**: Time range for comparison
    - **include_change_points**: Whether to include change points
    - **include_trends**: Whether to include trend analysis

    Returns comparative analysis with insights.
    """
    try:
        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Generate comparison data for each user and metric
        comparison_data = []
        similarity_matrix = []
        insights = []
        recommendations = []

        for user_id in request.user_ids:
            for metric in request.metrics:
                # Get user's progression analysis
                try:
                    analysis = await analyzer.analyze_user_progression(
                        user_id=user_id,
                        metrics=[metric],
                        time_range_days=request.time_range_days
                    )

                    if metric in analysis['metrics_analysis']:
                        user_data = {
                            'user_id': user_id,
                            'metric': metric,
                            'trend': analysis['metrics_analysis'][metric]['trend'],
                            'change_points': analysis['metrics_analysis'][metric]['change_points'],
                            'baseline': analysis['metrics_analysis'][metric].get('baseline'),
                            'current_value': analysis['metrics_analysis'][metric].get('current_value')
                        }
                        comparison_data.append(user_data)

                except Exception as e:
                    logger.error(f"Error analyzing user {user_id}, metric {metric}: {e}")
                    continue

        # Calculate similarity matrix (simplified)
        n_users = len(request.user_ids)
        similarity_matrix = [[1.0 for _ in range(n_users)] for _ in range(n_users)]

        for i in range(n_users):
            for j in range(i + 1, n_users):
                # Simple similarity calculation based on metrics
                user1_data = [d for d in comparison_data if d['user_id'] == request.user_ids[i] and d['metric'] in request.metrics]
                user2_data = [d for d in comparison_data if d['user_id'] == request.user_ids[j] and d['metric'] in request.metrics]

                if user1_data and user2_data:
                    # Compare trend directions
                    trend1 = user1_data[0]['trend']['trend_direction'] if user1_data and user1_data[0]['trend'] else 'stable'
                    trend2 = user2_data[0]['trend']['trend_direction'] if user2_data and user2_data[0]['trend'] else 'stable'

                    similarity = 1.0 if trend1 == trend2 else 0.5

                    # Adjust based on current values if available
                    if (user1_data[0].get('current_value') and user2_data[0].get('current_value')):
                        value1 = user1_data[0]['current_value']
                        value2 = user2_data[0]['current_value']
                        value_similarity = 1.0 - min(1.0, abs(value1 - value2) / max(value1, value2, 1))
                        similarity = (similarity + 0.5) / 2  # Average with trend similarity

                    similarity_matrix[i][j] = round(similarity, 2)
                    similarity_matrix[j][i] = similarity_matrix[i][j]

        # Generate insights and recommendations
        if similarity_matrix:
            # Find highly similar users
            for i in range(n_users):
                for j in range(i + 1, n_users):
                    if similarity_matrix[i][j] > 0.8:
                        insights.append({
                            'type': 'high_similarity',
                            'user1_id': request.user_ids[i],
                            'user2_id': request.user_ids[j],
                            'similarity': similarity_matrix[i][j],
                            'description': f"Users {request.user_ids[i]} and {request.user_ids[j]} show highly similar behavioral patterns"
                        })
                    elif similarity_matrix[i][j] < 0.3:
                        insights.append({
                            'type': 'low_similarity',
                            'user1_id': request.user_ids[i],
                            'user2_id': request.user_ids[j],
                            'similarity': similarity_matrix[i][j],
                            'description': f"Users {request.user_ids[i]} and {request.user_ids[j]} show divergent behavioral patterns"
                        })

        recommendations = [
            "Consider grouping similar users for targeted interventions",
            "Investigate divergent users for personalized support",
            "Leverage behavioral similarities in team formation"
        ]

        response_data = {
            'comparison_data': comparison_data,
            'similarity_matrix': similarity_matrix,
            'insights': insights,
            'recommendations': recommendations,
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'metadata': {
                'users_compared': request.user_ids,
                'metrics_compared': request.metrics,
                'time_range_days': request.time_range_days,
                'include_change_points': request.include_change_points,
                'include_trends': request.include_trends
            }
        }

        return response_data

    except Exception as e:
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing longitudinal data: {str(e)}"
        ) from e
@router.get("/insights/{user_id}")
async def get_user_insights(
    user_id: str,
    time_range: str = Query("90d", description="Time range for insights"),
    metrics: Optional[str] = Query(None, description="Comma-separated metrics to analyze"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get behavioral insights for a specific user.

    - **user_id**: User ID to get insights for
    - **time_range**: Time range for insights
    - **metrics**: Comma-separated metrics to analyze

    Returns user-specific behavioral insights and recommendations.
    """
    try:
        # Check permissions
        if user_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view insights for this user"
            )

        # Parse metrics
        metrics_list = []
        if metrics:
            metrics_list = [m.strip() for m in metrics.split(',') if m.strip()]

        # If no metrics specified, use default ones
        if not metrics_list:
            metrics_list = ['user_engagement', 'session_duration', 'task_completion']

        # Initialize longitudinal analyzer
        analyzer = LongitudinalAnalyzer(db)

        # Convert time range to days
        time_range_days = {
            "7d": 7,
            "30d": 30,
            "90d": 90,
            "180d": 180
        }.get(time_range, 90)

        # Get user insights
        progression_analysis = await analyzer.analyze_user_progression(
            user_id=user_id,
            metrics=metrics_list,
            time_range_days=time_range_days
        )

        # Filter insights to specific user
        user_insights = {
            'user_id': progression_analysis['user_id'],
            'insights': progression_analysis['overall_insights'],
            'recommendations': progression_analysis['recommendations'],
            'risk_indicators': progression_analysis['risk_indicators'],
            'metrics_summary': {
                metric: progression_analysis['metrics_analysis']
            },
            'time_range': time_range,
            'analysis_date': datetime.utcnow().isoformat()
        }

        return user_insights

    except Exception as e:
        raise HTTPException(
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting user insights: {str(e)}"
        ) from e

# Import numpy for mock data generation
import numpy as np
