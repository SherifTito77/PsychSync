"""
Analytics Dashboard Service
Comprehensive data aggregation and analytics service for PsychSync dashboards.
Provides real-time and historical analytics across multiple dimensions:
- User engagement and activity metrics
- Assessment completion and performance analytics
- Team dynamics and collaboration insights
- System performance and usage statistics
- Business metrics and KPI tracking
"""

from typing import List, Dict, Any, Optional, Tuple, Union
import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from enum import Enum
import json
import logging

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc, asc, text
from sqlalchemy.sql import select
import redis.asyncio as redis

# Note: These would be imported from your actual models
# from app.db.models.user import User
# from app.db.models.team import Team
# from app.db.models.assessment import Assessment
# from app.db.models.response import Response
# from app.db.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

class TimePeriod(Enum):
    """Time period options for analytics."""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    CUSTOM = "custom"

class MetricType(Enum):
    """Types of metrics available."""
    COUNTER = "counter"           # Simple count metrics
    AVERAGE = "average"           # Average value metrics
    SUM = "sum"                   # Sum metrics
    PERCENTAGE = "percentage"     # Percentage metrics
    RATIO = "ratio"              # Ratio metrics
    TREND = "trend"              # Trend analysis metrics
    DISTRIBUTION = "distribution" # Distribution metrics

@dataclass
class AnalyticsMetric:
    """Individual analytics metric definition."""
    name: str
    type: MetricType
    value: Union[int, float, str, Dict, List]
    label: str
    description: str
    format: Optional[str] = None
    target: Optional[float] = None
    trend: Optional[float] = None
    comparison_period: Optional[str] = None

@dataclass
class DashboardConfig:
    """Configuration for analytics dashboard."""

    # Time window settings
    default_time_period: TimePeriod = TimePeriod.LAST_30_DAYS
    cache_ttl: int = 300  # 5 minutes
    long_cache_ttl: int = 3600  # 1 hour for historical data

    # Data aggregation settings
    max_data_points: int = 1000
    sample_rate_large_datasets: float = 0.1  # 10% sampling for large datasets

    # Performance settings
    query_timeout: int = 30  # seconds
    concurrent_queries: int = 5

    # Redis configuration
    redis_url: str = "redis://localhost:6379/4"

class AnalyticsDashboard:
    """
    Comprehensive analytics dashboard service.
    """

    def __init__(self, db_session: Session, config: Optional[DashboardConfig] = None):
        self.db = db_session
        self.config = config or DashboardConfig()
        self.redis_client: Optional[redis.Redis] = None
        self._init_redis()

        # Predefined metric definitions
        self.metric_definitions = {
            'user_metrics': [
                'total_users', 'active_users', 'new_users', 'user_retention_rate',
                'user_engagement_score', 'average_session_duration', 'user_growth_rate'
            ],
            'assessment_metrics': [
                'total_assessments', 'completed_assessments', 'assessment_completion_rate',
                'average_assessment_score', 'assessment_completion_time', 'popular_assessments'
            ],
            'team_metrics': [
                'total_teams', 'active_teams', 'average_team_size', 'team_collaboration_score',
                'team_performance_index', 'cross_team_collaboration'
            ],
            'system_metrics': [
                'api_requests', 'response_time_avg', 'error_rate', 'uptime_percentage',
                'database_connections', 'cache_hit_rate', 'storage_usage'
            ],
            'business_metrics': [
                'revenue_mrr', 'conversion_rate', 'churn_rate', 'customer_acquisition_cost',
                'lifetime_value', 'monthly_growth_rate', 'feature_adoption_rate'
            ]
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
            logger.info("Analytics dashboard Redis connection established")
        except Exception as e:
            logger.warning(f"Could not connect to Redis for analytics caching: {e}")
            self.redis_client = None

    async def get_dashboard_overview(
        self,
        time_period: TimePeriod = TimePeriod.LAST_30_DAYS,
        organization_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive dashboard overview with key metrics.
        """
        try:
            cache_key = f"dashboard:overview:{time_period.value}:{organization_id}:{team_id}"

            # Try cache first
            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)

            # Generate metrics concurrently
            tasks = [
                self._get_user_metrics(time_period, organization_id, team_id),
                self._get_assessment_metrics(time_period, organization_id, team_id),
                self._get_team_metrics(time_period, organization_id, team_id),
                self._get_system_metrics(time_period),
                self._get_business_metrics(time_period, organization_id)
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            overview = {
                'period': time_period.value,
                'generated_at': datetime.utcnow().isoformat(),
                'user_metrics': results[0] if not isinstance(results[0], Exception) else {},
                'assessment_metrics': results[1] if not isinstance(results[1], Exception) else {},
                'team_metrics': results[2] if not isinstance(results[2], Exception) else {},
                'system_metrics': results[3] if not isinstance(results[3], Exception) else {},
                'business_metrics': results[4] if not isinstance(results[4], Exception) else {},
                'summary': await self._generate_summary(results)
            }

            # Cache results
            if self.redis_client:
                await self.redis_client.setex(
                    cache_key,
                    self.config.cache_ttl,
                    json.dumps(overview, default=str)
                )

            return overview

        except Exception as e:
            logger.error(f"Error generating dashboard overview: {e}")
            return self._get_empty_overview(time_period)

    async def get_time_series_data(
        self,
        metric: str,
        time_period: TimePeriod = TimePeriod.LAST_30_DAYS,
        granularity: str = "day",  # hour, day, week, month
        organization_id: Optional[str] = None,
        team_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get time series data for a specific metric.
        """
        try:
            cache_key = f"timeseries:{metric}:{time_period.value}:{granularity}:{organization_id}:{team_id}"

            if self.redis_client:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    return json.loads(cached_data)

            time_series = await self._generate_time_series(
                metric, time_period, granularity, organization_id, team_id
            )

            # Cache with longer TTL for historical data
            if self.redis_client:
                ttl = self.config.long_cache_ttl if time_period in [TimePeriod.LAST_90_DAYS, TimePeriod.THIS_YEAR] else self.config.cache_ttl
                await self.redis_client.setex(cache_key, ttl, json.dumps(time_series, default=str))

            return time_series

        except Exception as e:
            logger.error(f"Error generating time series data for {metric}: {e}")
            return self._get_empty_time_series(metric, time_period)

    async def get_analytics_insights(
        self,
        time_period: TimePeriod = TimePeriod.LAST_30_DAYS,
        organization_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered insights from analytics data.
        """
        try:
            insights = {
                'user_insights': await self._generate_user_insights(time_period, organization_id),
                'assessment_insights': await self._generate_assessment_insights(time_period, organization_id),
                'team_insights': await self._generate_team_insights(time_period, organization_id),
                'recommendations': await self._generate_recommendations(time_period, organization_id),
                'anomalies': await self._detect_anomalies(time_period, organization_id),
                'predictions': await self._generate_predictions(time_period, organization_id)
            }

            return insights

        except Exception as e:
            logger.error(f"Error generating analytics insights: {e}")
            return self._get_empty_insights()

    async def _get_user_metrics(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str],
        team_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get user-related metrics."""
        try:
            # Note: These would be actual database queries using your models
            # For now, we'll use placeholder implementations

            date_range = self._get_date_range(time_period)

            # Simulate database queries with mock data
            metrics = {
                'total_users': 1500,
                'active_users': 875,
                'new_users': 142,
                'user_retention_rate': 0.78,
                'user_engagement_score': 7.2,
                'average_session_duration': 25.5,  # minutes
                'user_growth_rate': 0.12,  # 12% growth
                'daily_active_users': [
                    {'date': (datetime.utcnow() - timedelta(days=i)).strftime('%Y-%m-%d'),
                     'users': 800 + np.random.randint(-50, 100)}
                    for i in range(30, 0, -1)
                ]
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting user metrics: {e}")
            return {}

    async def _get_assessment_metrics(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str],
        team_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get assessment-related metrics."""
        try:
            metrics = {
                'total_assessments': 3240,
                'completed_assessments': 2890,
                'assessment_completion_rate': 0.89,
                'average_assessment_score': 78.5,
                'assessment_completion_time': 15.2,  # minutes
                'popular_assessments': [
                    {'name': 'Big Five Personality', 'completions': 892},
                    {'name': 'Team Compatibility', 'completions': 654},
                    {'name': 'Leadership Style', 'completions': 432}
                ],
                'assessment_types': {
                    'personality': 1200,
                    'team_dynamics': 980,
                    'leadership': 650,
                    'skills': 410
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting assessment metrics: {e}")
            return {}

    async def _get_team_metrics(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str],
        team_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get team-related metrics."""
        try:
            metrics = {
                'total_teams': 245,
                'active_teams': 198,
                'average_team_size': 8.2,
                'team_collaboration_score': 8.1,
                'team_performance_index': 7.8,
                'cross_team_collaboration': 0.65,
                'team_health_distribution': {
                    'excellent': 0.25,
                    'good': 0.45,
                    'moderate': 0.20,
                    'needs_improvement': 0.10
                }
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting team metrics: {e}")
            return {}

    async def _get_system_metrics(self, time_period: TimePeriod) -> Dict[str, Any]:
        """Get system performance metrics."""
        try:
            metrics = {
                'api_requests': 2840000,
                'response_time_avg': 245,  # milliseconds
                'error_rate': 0.002,  # 0.2%
                'uptime_percentage': 99.97,
                'database_connections': 45,
                'cache_hit_rate': 0.92,
                'storage_usage': 0.68,  # 68% used
                'system_health': 'excellent'
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}

    async def _get_business_metrics(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> Dict[str, Any]:
        """Get business metrics."""
        try:
            metrics = {
                'revenue_mrr': 48500,  # Monthly recurring revenue
                'conversion_rate': 0.085,  # 8.5%
                'churn_rate': 0.032,  # 3.2%
                'customer_acquisition_cost': 285,
                'lifetime_value': 2400,
                'monthly_growth_rate': 0.12,  # 12%
                'feature_adoption_rate': 0.67,  # 67%
                'customer_satisfaction': 8.4  # out of 10
            }

            return metrics

        except Exception as e:
            logger.error(f"Error getting business metrics: {e}")
            return {}

    async def _generate_time_series(
        self,
        metric: str,
        time_period: TimePeriod,
        granularity: str,
        organization_id: Optional[str],
        team_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate time series data for a metric."""
        try:
            date_range = self._get_date_range(time_period)

            # Generate mock time series data
            if granularity == "day":
                dates = pd.date_range(
                    start=date_range['start'],
                    end=date_range['end'],
                    freq='D'
                )
            elif granularity == "week":
                dates = pd.date_range(
                    start=date_range['start'],
                    end=date_range['end'],
                    freq='W'
                )
            else:  # month
                dates = pd.date_range(
                    start=date_range['start'],
                    end=date_range['end'],
                    freq='M'
                )

            # Generate mock values with trend and noise
            base_values = {
                'active_users': 800,
                'completed_assessments': 120,
                'api_requests': 50000,
                'revenue_mrr': 45000
            }

            base_value = base_values.get(metric, 100)

            data_points = []
            for date in dates:
                # Add trend and seasonal variation
                trend_factor = 1 + (date - dates[0]).days * 0.001  # Small upward trend
                seasonal_factor = 1 + 0.2 * np.sin(2 * np.pi * date.dayofyear / 365)  # Seasonal variation
                noise_factor = np.random.normal(1, 0.1)  # Random noise

                value = base_value * trend_factor * seasonal_factor * noise_factor
                value = max(0, value)  # Ensure non-negative

                data_points.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'value': round(value, 2)
                })

            return {
                'metric': metric,
                'period': time_period.value,
                'granularity': granularity,
                'data_points': data_points,
                'summary': self._calculate_time_series_summary(data_points)
            }

        except Exception as e:
            logger.error(f"Error generating time series: {e}")
            return self._get_empty_time_series(metric, time_period)

    async def _generate_user_insights(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate user behavior insights."""
        insights = [
            {
                'type': 'positive',
                'title': 'Strong User Engagement',
                'description': 'User engagement has increased by 15% compared to last period',
                'metric': 'user_engagement_score',
                'change': 0.15,
                'recommendation': 'Continue focusing on features that drive engagement'
            },
            {
                'type': 'concern',
                'title': 'Slight Drop in Retention',
                'description': 'User retention decreased by 3% from last month',
                'metric': 'user_retention_rate',
                'change': -0.03,
                'recommendation': 'Investigate onboarding process and user experience'
            }
        ]
        return insights

    async def _generate_assessment_insights(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate assessment-related insights."""
        insights = [
            {
                'type': 'positive',
                'title': 'High Assessment Completion',
                'description': '89% assessment completion rate is above industry average',
                'metric': 'assessment_completion_rate',
                'value': 0.89,
                'recommendation': 'Assessment design is effective - consider expanding catalog'
            }
        ]
        return insights

    async def _generate_team_insights(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate team dynamics insights."""
        insights = [
            {
                'type': 'opportunity',
                'title': 'Cross-Team Collaboration Potential',
                'description': 'Only 65% of teams engage in cross-team collaboration',
                'metric': 'cross_team_collaboration',
                'value': 0.65,
                'recommendation': 'Create more opportunities for inter-team projects'
            }
        ]
        return insights

    async def _generate_recommendations(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Generate actionable recommendations."""
        return [
            {
                'priority': 'high',
                'category': 'user_experience',
                'title': 'Optimize Mobile Experience',
                'description': 'Mobile users show 20% lower engagement metrics',
                'expected_impact': '15% increase in mobile engagement',
                'effort': 'medium',
                'timeline': '2-3 weeks'
            },
            {
                'priority': 'medium',
                'category': 'product',
                'title': 'Launch Team Assessment Bundle',
                'description': 'Package multiple assessments for teams at discounted rate',
                'expected_impact': '25% increase in team assessment sales',
                'effort': 'low',
                'timeline': '1-2 weeks'
            }
        ]

    async def _detect_anomalies(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in metrics."""
        return [
            {
                'metric': 'api_requests',
                'anomaly_type': 'spike',
                'description': 'Unusual spike in API requests on 2024-01-15',
                'severity': 'medium',
                'investigation_required': True
            }
        ]

    async def _generate_predictions(
        self,
        time_period: TimePeriod,
        organization_id: Optional[str]
    ) -> Dict[str, Any]:
        """Generate predictions for future metrics."""
        return {
            'next_month_predictions': {
                'active_users': 950,
                'revenue_mrr': 52000,
                'new_teams': 12
            },
            'confidence_level': 0.85,
            'model_version': 'v2.1'
        }

    def _get_date_range(self, time_period: TimePeriod) -> Dict[str, datetime]:
        """Get date range for time period."""
        now = datetime.utcnow()

        if time_period == TimePeriod.TODAY:
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == TimePeriod.YESTERDAY:
            yesterday = now - timedelta(days=1)
            start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            end = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)
            return {'start': start, 'end': end}
        elif time_period == TimePeriod.LAST_7_DAYS:
            start = now - timedelta(days=7)
        elif time_period == TimePeriod.LAST_30_DAYS:
            start = now - timedelta(days=30)
        elif time_period == TimePeriod.LAST_90_DAYS:
            start = now - timedelta(days=90)
        elif time_period == TimePeriod.THIS_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif time_period == TimePeriod.LAST_MONTH:
            first_day_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            start = first_day_this_month - timedelta(days=1)
            start = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = first_day_this_month - timedelta(microseconds=1)
            return {'start': start, 'end': end}
        else:
            start = now - timedelta(days=30)

        return {'start': start, 'end': now}

    def _calculate_time_series_summary(self, data_points: List[Dict]) -> Dict[str, float]:
        """Calculate summary statistics for time series data."""
        if not data_points:
            return {}

        values = [point['value'] for point in data_points]
        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'trend': (values[-1] - values[0]) / len(values) if len(values) > 1 else 0
        }

    async def _generate_summary(self, results: List) -> Dict[str, Any]:
        """Generate executive summary from all metrics."""
        try:
            # Extract key metrics from results
            user_growth = 0.12  # Mock data
            assessment_completion = 0.89
            team_health = 8.1
            system_health = 99.97
            revenue_growth = 0.12

            # Determine overall health
            health_score = (user_growth + assessment_completion + (team_health/10) + (system_health/100) + revenue_growth) / 5

            return {
                'overall_health_score': round(health_score, 2),
                'key_highlights': [
                    f"{assessment_completion:.1%} assessment completion rate",
                    f"{system_health:.1f}% system uptime",
                    f"{user_growth:.1%} user growth",
                    f"${results[4].get('revenue_mrr', 0):,.0f} monthly recurring revenue"
                ],
                'areas_of_focus': [
                    'Mobile experience optimization',
                    'Cross-team collaboration improvement',
                    'User retention enhancement'
                ],
                'health_status': self._get_health_status(health_score)
            }

        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {}

    def _get_health_status(self, score: float) -> str:
        """Get health status based on score."""
        if score >= 0.8:
            return "excellent"
        elif score >= 0.7:
            return "good"
        elif score >= 0.6:
            return "moderate"
        else:
            return "needs_improvement"

    def _get_empty_overview(self, time_period: TimePeriod) -> Dict[str, Any]:
        """Get empty overview structure."""
        return {
            'period': time_period.value,
            'generated_at': datetime.utcnow().isoformat(),
            'user_metrics': {},
            'assessment_metrics': {},
            'team_metrics': {},
            'system_metrics': {},
            'business_metrics': {},
            'summary': {}
        }

    def _get_empty_time_series(self, metric: str, time_period: TimePeriod) -> Dict[str, Any]:
        """Get empty time series structure."""
        return {
            'metric': metric,
            'period': time_period.value,
            'data_points': [],
            'summary': {}
        }

    def _get_empty_insights(self) -> Dict[str, Any]:
        """Get empty insights structure."""
        return {
            'user_insights': [],
            'assessment_insights': [],
            'team_insights': [],
            'recommendations': [],
            'anomalies': [],
            'predictions': {}
        }

class AnalyticsCacheManager:
    """
    Manages caching for analytics dashboard service.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def invalidate_cache_pattern(self, pattern: str) -> None:
        """Invalidate cache entries matching pattern."""
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                await self.redis.delete(*keys)
                logger.info(f"Invalidated {len(keys)} cache entries for pattern: {pattern}")
        except Exception as e:
            logger.error(f"Error invalidating cache pattern {pattern}: {e}")

    async def warm_cache(self, dashboard_service: AnalyticsDashboard) -> None:
        """Warm cache with common dashboard queries."""
        try:
            common_queries = [
                (TimePeriod.LAST_7_DAYS, None, None),
                (TimePeriod.LAST_30_DAYS, None, None),
                (TimePeriod.THIS_MONTH, None, None)
            ]

            for period, org_id, team_id in common_queries:
                await dashboard_service.get_dashboard_overview(period, org_id, team_id)

            logger.info("Analytics cache warmed successfully")

        except Exception as e:
            logger.error(f"Error warming analytics cache: {e}")