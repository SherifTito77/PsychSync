"""
Monitoring Dashboard Service
Provides comprehensive dashboard functionality for visualizing system health,
performance metrics, and monitoring data from all sources.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.services.sentry_service import SentryService
from app.services.apm_service import APMService, MetricType, AlertSeverity
from app.services.alerts_service import AlertsService, AlertStatus, NotificationChannel

logger = logging.getLogger(__name__)


class DashboardType(Enum):
    """Types of dashboards available"""
    SYSTEM_OVERVIEW = "system_overview"
    PERFORMANCE = "performance"
    ERRORS = "errors"
    ALERTS = "alerts"
    BUSINESS = "business"
    INFRASTRUCTURE = "infrastructure"
    CUSTOM = "custom"


class TimeRange(Enum):
    """Standard time ranges for dashboard data"""
    LAST_1H = "1h"
    LAST_6H = "6h"
    LAST_24H = "24h"
    LAST_7D = "7d"
    LAST_30D = "30d"
    CUSTOM = "custom"


class ChartType(Enum):
    """Types of charts supported"""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    AREA = "area"
    SCATTER = "scatter"
    GAUGE = "gauge"
    TABLE = "table"
    STAT = "stat"
    HEATMAP = "heatmap"


@dataclass
class DataPoint:
    """Single data point for time series data"""
    timestamp: datetime
    value: Union[float, int]
    labels: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "value": self.value,
            "labels": self.labels
        }


@dataclass
class MetricSeries:
    """Time series data for a metric"""
    name: str
    data_points: List[DataPoint] = field(default_factory=list)
    unit: str = ""
    chart_type: ChartType = ChartType.LINE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "data_points": [dp.to_dict() for dp in self.data_points],
            "unit": self.unit,
            "chart_type": self.chart_type.value
        }


@dataclass
class DashboardWidget:
    """Individual widget on a dashboard"""
    id: str
    title: str
    type: ChartType
    position: Dict[str, int]  # x, y, width, height
    query: Dict[str, Any]
    time_range: TimeRange = TimeRange.LAST_24H
    refresh_interval: int = 60  # seconds
    data: Optional[Union[MetricSeries, List[MetricSeries], Dict[str, Any]]] = None
    last_updated: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "type": self.type.value,
            "position": self.position,
            "query": self.query,
            "time_range": self.time_range.value,
            "refresh_interval": self.refresh_interval,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "data": self.data.to_dict() if isinstance(self.data, MetricSeries) else
                   [ds.to_dict() for ds in self.data] if isinstance(self.data, list) else
                   self.data
        }


@dataclass
class Dashboard:
    """Complete dashboard configuration"""
    id: str
    name: str
    type: DashboardType
    description: str
    widgets: List[DashboardWidget] = field(default_factory=list)
    filters: Dict[str, Any] = field(default_factory=dict)
    permissions: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "widgets": [widget.to_dict() for widget in self.widgets],
            "filters": self.filters,
            "permissions": self.permissions,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }


class DashboardService:
    """Comprehensive dashboard service for monitoring data visualization"""

    def __init__(self):
        self.sentry_service = SentryService()
        self.apm_service = APMService()
        self.alerts_service = AlertsService()

        # In-memory cache for dashboard data
        self._dashboard_cache = {}
        self._cache_ttl = 300  # 5 minutes

        # Background tasks for data refresh
        self._refresh_tasks = {}
        self._running = False

        # Pre-built dashboards
        self._builtin_dashboards = self._create_builtin_dashboards()

        logger.info("Dashboard service initialized")

    def _create_builtin_dashboards(self) -> Dict[str, Dashboard]:
        """Create built-in dashboard templates"""
        dashboards = {}

        # System Overview Dashboard
        system_dashboard = Dashboard(
            id="system_overview",
            name="System Overview",
            type=DashboardType.SYSTEM_OVERVIEW,
            description="High-level system health and performance metrics",
            widgets=[
                DashboardWidget(
                    id="system_health",
                    title="System Health",
                    type=ChartType.GAUGE,
                    position={"x": 0, "y": 0, "width": 4, "height": 2},
                    query={"metric": "system_health_score"}
                ),
                DashboardWidget(
                    id="error_rate",
                    title="Error Rate",
                    type=ChartType.LINE,
                    position={"x": 4, "y": 0, "width": 4, "height": 2},
                    query={"metric": "error_rate"}
                ),
                DashboardWidget(
                    id="response_time",
                    title="Average Response Time",
                    type=ChartType.LINE,
                    position={"x": 8, "y": 0, "width": 4, "height": 2},
                    query={"metric": "response_time"}
                ),
                DashboardWidget(
                    id="active_users",
                    title="Active Users",
                    type=ChartType.STAT,
                    position={"x": 0, "y": 2, "width": 3, "height": 2},
                    query={"metric": "active_users"}
                ),
                DashboardWidget(
                    id="request_rate",
                    title="Request Rate",
                    type=ChartType.LINE,
                    position={"x": 3, "y": 2, "width": 5, "height": 2},
                    query={"metric": "request_rate"}
                ),
                DashboardWidget(
                    id="top_errors",
                    title="Top Errors",
                    type=ChartType.TABLE,
                    position={"x": 8, "y": 2, "width": 4, "height": 2},
                    query={"metric": "top_errors"}
                )
            ]
        )

        # Performance Dashboard
        performance_dashboard = Dashboard(
            id="performance",
            name="Performance Metrics",
            type=DashboardType.PERFORMANCE,
            description="Detailed application performance metrics",
            widgets=[
                DashboardWidget(
                    id="response_time_distribution",
                    title="Response Time Distribution",
                    type=ChartType.HISTOGRAM,
                    position={"x": 0, "y": 0, "width": 6, "height": 3},
                    query={"metric": "response_time_histogram"}
                ),
                DashboardWidget(
                    id="throughput",
                    title="Throughput",
                    type=ChartType.AREA,
                    position={"x": 6, "y": 0, "width": 6, "height": 3},
                    query={"metric": "throughput"}
                ),
                DashboardWidget(
                    id="slow_requests",
                    title="Slow Requests",
                    type=ChartType.TABLE,
                    position={"x": 0, "y": 3, "width": 6, "height": 3},
                    query={"metric": "slow_requests"}
                ),
                DashboardWidget(
                    id="apm_score",
                    title="APM Score",
                    type=ChartType.GAUGE,
                    position={"x": 6, "y": 3, "width": 3, "height": 3},
                    query={"metric": "apm_score"}
                ),
                DashboardWidget(
                    id="cpu_usage",
                    title="CPU Usage",
                    type=ChartType.LINE,
                    position={"x": 9, "y": 3, "width": 3, "height": 3},
                    query={"metric": "cpu_usage"}
                )
            ]
        )

        # Errors Dashboard
        errors_dashboard = Dashboard(
            id="errors",
            name="Error Analysis",
            type=DashboardType.ERRORS,
            description="Error tracking and analysis dashboard",
            widgets=[
                DashboardWidget(
                    id="error_trend",
                    title="Error Trend",
                    type=ChartType.LINE,
                    position={"x": 0, "y": 0, "width": 8, "height": 2},
                    query={"metric": "error_trend"}
                ),
                DashboardWidget(
                    id="error_breakdown",
                    title="Error Types",
                    type=ChartType.PIE,
                    position={"x": 8, "y": 0, "width": 4, "height": 2},
                    query={"metric": "error_types"}
                ),
                DashboardWidget(
                    id="recent_errors",
                    title="Recent Errors",
                    type=ChartType.TABLE,
                    position={"x": 0, "y": 2, "width": 12, "height": 4},
                    query={"metric": "recent_errors"}
                )
            ]
        )

        dashboards["system_overview"] = system_dashboard
        dashboards["performance"] = performance_dashboard
        dashboards["errors"] = errors_dashboard

        return dashboards

    async def get_dashboard(
        self,
        dashboard_id: str,
        time_range: Optional[TimeRange] = None,
        filters: Optional[Dict[str, Any]] = None,
        refresh_data: bool = False
    ) -> Optional[Dashboard]:
        """Get dashboard with current data"""
        # Get dashboard configuration
        if dashboard_id in self._builtin_dashboards:
            dashboard = self._builtin_dashboards[dashboard_id]
        else:
            # TODO: Load custom dashboard from database
            return None

        # Update time range if provided
        if time_range:
            for widget in dashboard.widgets:
                widget.time_range = time_range

        # Apply filters
        if filters:
            dashboard.filters.update(filters)

        # Refresh widget data
        if refresh_data:
            await self._refresh_dashboard_data(dashboard)
        elif self._is_cache_expired(dashboard_id):
            await self._refresh_dashboard_data(dashboard)
        else:
            dashboard = self._get_cached_dashboard(dashboard_id) or dashboard

        return dashboard

    async def create_custom_dashboard(
        self,
        name: str,
        description: str,
        widgets: List[Dict[str, Any]],
        permissions: Optional[List[str]] = None
    ) -> Dashboard:
        """Create a custom dashboard"""
        # Create dashboard object
        dashboard = Dashboard(
            id=f"custom_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            name=name,
            type=DashboardType.CUSTOM,
            description=description,
            permissions=permissions or []
        )

        # Convert widget dictionaries to DashboardWidget objects
        for widget_data in widgets:
            widget = DashboardWidget(
                id=widget_data["id"],
                title=widget_data["title"],
                type=ChartType(widget_data["type"]),
                position=widget_data["position"],
                query=widget_data["query"],
                time_range=TimeRange(widget_data.get("time_range", "24h")),
                refresh_interval=widget_data.get("refresh_interval", 60)
            )
            dashboard.widgets.append(widget)

        # TODO: Save to database
        self._builtin_dashboards[dashboard.id] = dashboard

        logger.info(f"Created custom dashboard: {dashboard.id}")
        return dashboard

    async def update_dashboard(
        self,
        dashboard_id: str,
        updates: Dict[str, Any]
    ) -> bool:
        """Update dashboard configuration"""
        if dashboard_id not in self._builtin_dashboards:
            return False

        dashboard = self._builtin_dashboards[dashboard_id]

        # Update allowed fields
        if "name" in updates:
            dashboard.name = updates["name"]
        if "description" in updates:
            dashboard.description = updates["description"]
        if "widgets" in updates:
            # Update widgets
            dashboard.widgets = []
            for widget_data in updates["widgets"]:
                widget = DashboardWidget(
                    id=widget_data["id"],
                    title=widget_data["title"],
                    type=ChartType(widget_data["type"]),
                    position=widget_data["position"],
                    query=widget_data["query"],
                    time_range=TimeRange(widget_data.get("time_range", "24h")),
                    refresh_interval=widget_data.get("refresh_interval", 60)
                )
                dashboard.widgets.append(widget)

        dashboard.updated_at = datetime.utcnow()

        # Clear cache
        self._clear_cache(dashboard_id)

        logger.info(f"Updated dashboard: {dashboard_id}")
        return True

    async def delete_dashboard(self, dashboard_id: str) -> bool:
        """Delete a dashboard"""
        if dashboard_id not in self._builtin_dashboards:
            return False

        # Don't allow deletion of built-in dashboards
        if self._builtin_dashboards[dashboard_id].type != DashboardType.CUSTOM:
            return False

        del self._builtin_dashboards[dashboard_id]
        self._clear_cache(dashboard_id)

        logger.info(f"Deleted dashboard: {dashboard_id}")
        return True

    async def list_dashboards(
        self,
        dashboard_type: Optional[DashboardType] = None
    ) -> List[Dashboard]:
        """List available dashboards"""
        dashboards = list(self._builtin_dashboards.values())

        if dashboard_type:
            dashboards = [d for d in dashboards if d.type == dashboard_type]

        return dashboards

    async def _refresh_dashboard_data(self, dashboard: Dashboard) -> None:
        """Refresh data for all widgets in a dashboard"""
        tasks = []
        for widget in dashboard.widgets:
            tasks.append(self._refresh_widget_data(widget))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Cache the dashboard
        self._cache_dashboard(dashboard)

        logger.debug(f"Refreshed data for dashboard: {dashboard.id}")

    async def _refresh_widget_data(self, widget: DashboardWidget) -> None:
        """Refresh data for a single widget"""
        try:
            widget_data = await self._query_widget_data(widget)
            widget.data = widget_data
            widget.last_updated = datetime.utcnow()
        except Exception as e:
            logger.error(f"Failed to refresh widget {widget.id}: {str(e)}")
            widget.data = None

    async def _query_widget_data(
        self,
        widget: DashboardWidget
    ) -> Union[MetricSeries, List[MetricSeries], Dict[str, Any]]:
        """Query data for a widget based on its query configuration"""
        query = widget.query
        metric = query.get("metric")

        # Calculate time range
        end_time = datetime.utcnow()
        start_time = self._calculate_start_time(widget.time_range, end_time)

        if metric == "system_health_score":
            return await self._get_system_health_score(start_time, end_time)
        elif metric == "error_rate":
            return await self._get_error_rate_trend(start_time, end_time)
        elif metric == "response_time":
            return await self._get_response_time_trend(start_time, end_time)
        elif metric == "active_users":
            return await self._get_active_users_count(start_time, end_time)
        elif metric == "request_rate":
            return await self._get_request_rate_trend(start_time, end_time)
        elif metric == "top_errors":
            return await self._get_top_errors(start_time, end_time)
        elif metric == "response_time_histogram":
            return await self._get_response_time_distribution(start_time, end_time)
        elif metric == "throughput":
            return await self._get_throughput_trend(start_time, end_time)
        elif metric == "slow_requests":
            return await self._get_slow_requests(start_time, end_time)
        elif metric == "apm_score":
            return await self._get_apm_score(start_time, end_time)
        elif metric == "cpu_usage":
            return await self._get_cpu_usage_trend(start_time, end_time)
        elif metric == "error_trend":
            return await self._get_error_trend(start_time, end_time)
        elif metric == "error_types":
            return await self._get_error_types_breakdown(start_time, end_time)
        elif metric == "recent_errors":
            return await self._get_recent_errors(start_time, end_time)
        else:
            # Default: return empty data
            return {"error": f"Unknown metric: {metric}"}

    async def _get_system_health_score(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Calculate overall system health score"""
        try:
            # Get various health indicators
            error_rate = await self._calculate_error_rate(start_time, end_time)
            response_time = await self._calculate_avg_response_time(start_time, end_time)
            uptime = await self._calculate_uptime(start_time, end_time)

            # Calculate health score (0-100)
            health_score = 100

            # Penalize for high error rate (>5%)
            if error_rate > 5:
                health_score -= min(40, error_rate * 8)

            # Penalize for slow response time (>500ms)
            if response_time > 500:
                health_score -= min(30, (response_time - 500) / 100)

            # Penalize for low uptime (<99%)
            if uptime < 99:
                health_score -= (99 - uptime) * 5

            health_score = max(0, min(100, health_score))

            return {
                "value": health_score,
                "status": "healthy" if health_score >= 90 else
                         "warning" if health_score >= 70 else "critical",
                "factors": {
                    "error_rate": error_rate,
                    "response_time": response_time,
                    "uptime": uptime
                }
            }
        except Exception as e:
            logger.error(f"Failed to calculate system health score: {str(e)}")
            return {"value": 0, "status": "unknown"}

    async def _get_error_rate_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get error rate trend over time"""
        try:
            # Get error data from Sentry
            error_data = await self._get_sentry_error_trend(start_time, end_time)

            data_points = []
            for timestamp, error_count, total_requests in error_data:
                error_rate = (error_count / total_requests * 100) if total_requests > 0 else 0
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    value=error_rate
                ))

            return MetricSeries(
                name="Error Rate (%)",
                data_points=data_points,
                unit="percent"
            )
        except Exception as e:
            logger.error(f"Failed to get error rate trend: {str(e)}")
            return MetricSeries(name="Error Rate (%)", data_points=[], unit="percent")

    async def _get_response_time_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get response time trend over time"""
        try:
            response_data = await self.apm_service.get_performance_trends(
                start_time=start_time,
                end_time=end_time
            )

            data_points = []
            for timestamp, response_time in response_data:
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    value=response_time
                ))

            return MetricSeries(
                name="Response Time",
                data_points=data_points,
                unit="ms"
            )
        except Exception as e:
            logger.error(f"Failed to get response time trend: {str(e)}")
            return MetricSeries(name="Response Time", data_points=[], unit="ms")

    async def _get_active_users_count(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get count of active users in the time range"""
        try:
            # TODO: Query actual user activity data
            # For now, return mock data
            return {
                "value": 1247,
                "trend": "+12%",
                "period": "vs last period"
            }
        except Exception as e:
            logger.error(f"Failed to get active users count: {str(e)}")
            return {"value": 0, "trend": "N/A"}

    async def _get_request_rate_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get request rate trend over time"""
        try:
            request_data = await self.apm_service.get_request_rate(
                start_time=start_time,
                end_time=end_time
            )

            data_points = []
            for timestamp, rate in request_data:
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    value=rate
                ))

            return MetricSeries(
                name="Request Rate",
                data_points=data_points,
                unit="req/s"
            )
        except Exception as e:
            logger.error(f"Failed to get request rate trend: {str(e)}")
            return MetricSeries(name="Request Rate", data_points=[], unit="req/s")

    async def _get_top_errors(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get top errors by frequency"""
        try:
            # Get errors from Sentry
            errors = await self._get_sentry_top_errors(start_time, end_time)

            return [
                {
                    "error_type": error["type"],
                    "message": error["message"][:100],  # Truncate long messages
                    "count": error["count"],
                    "last_seen": error["last_seen"]
                }
                for error in errors[:10]  # Top 10 errors
            ]
        except Exception as e:
            logger.error(f"Failed to get top errors: {str(e)}")
            return []

    async def _get_response_time_distribution(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get response time distribution histogram"""
        try:
            # Get histogram data from APM service
            distribution = await self.apm_service.get_response_time_distribution(
                start_time=start_time,
                end_time=end_time
            )

            return {
                "buckets": distribution["buckets"],
                "counts": distribution["counts"],
                "percentiles": distribution["percentiles"]
            }
        except Exception as e:
            logger.error(f"Failed to get response time distribution: {str(e)}")
            return {"buckets": [], "counts": [], "percentiles": {}}

    async def _get_throughput_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get throughput trend over time"""
        try:
            throughput_data = await self.apm_service.get_throughput_metrics(
                start_time=start_time,
                end_time=end_time
            )

            data_points = []
            for timestamp, throughput in throughput_data:
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    value=throughput
                ))

            return MetricSeries(
                name="Throughput",
                data_points=data_points,
                unit="ops/min"
            )
        except Exception as e:
            logger.error(f"Failed to get throughput trend: {str(e)}")
            return MetricSeries(name="Throughput", data_points=[], unit="ops/min")

    async def _get_slow_requests(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get slowest requests"""
        try:
            slow_requests = await self.apm_service.get_slow_requests(
                start_time=start_time,
                end_time=end_time,
                limit=20
            )

            return [
                {
                    "endpoint": req["endpoint"],
                    "method": req["method"],
                    "response_time": req["response_time"],
                    "timestamp": req["timestamp"],
                    "status_code": req["status_code"]
                }
                for req in slow_requests
            ]
        except Exception as e:
            logger.error(f"Failed to get slow requests: {str(e)}")
            return []

    async def _get_apm_score(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get APM health score"""
        try:
            score = await self.apm_service.get_health_score(
                start_time=start_time,
                end_time=end_time
            )

            return {
                "value": score["score"],
                "status": score["status"],
                "factors": score["factors"]
            }
        except Exception as e:
            logger.error(f"Failed to get APM score: {str(e)}")
            return {"value": 0, "status": "unknown"}

    async def _get_cpu_usage_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get CPU usage trend"""
        try:
            cpu_data = await self.apm_service.get_system_metrics(
                start_time=start_time,
                end_time=end_time,
                metric="cpu"
            )

            data_points = []
            for timestamp, cpu_usage in cpu_data:
                data_points.append(DataPoint(
                    timestamp=timestamp,
                    value=cpu_usage
                ))

            return MetricSeries(
                name="CPU Usage",
                data_points=data_points,
                unit="percent"
            )
        except Exception as e:
            logger.error(f"Failed to get CPU usage trend: {str(e)}")
            return MetricSeries(name="CPU Usage", data_points=[], unit="percent")

    async def _get_error_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> MetricSeries:
        """Get detailed error trend"""
        return await self._get_error_rate_trend(start_time, end_time)

    async def _get_error_types_breakdown(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get breakdown of error types"""
        try:
            error_types = await self._get_sentry_error_types(start_time, end_time)

            return [
                {
                    "name": error_type["type"],
                    "value": error_type["count"],
                    "percentage": error_type["percentage"]
                }
                for error_type in error_types
            ]
        except Exception as e:
            logger.error(f"Failed to get error types breakdown: {str(e)}")
            return []

    async def _get_recent_errors(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Get recent errors with details"""
        try:
            recent_errors = await self._get_sentry_recent_errors(start_time, end_time)

            return [
                {
                    "timestamp": error["timestamp"],
                    "level": error["level"],
                    "error_type": error["type"],
                    "message": error["message"][:200],  # Truncate
                    "environment": error["environment"],
                    "release": error.get("release", "unknown")
                }
                for error in recent_errors[:50]  # Last 50 errors
            ]
        except Exception as e:
            logger.error(f"Failed to get recent errors: {str(e)}")
            return []

    # Helper methods for data calculation and time handling

    def _calculate_start_time(
        self,
        time_range: TimeRange,
        end_time: datetime
    ) -> datetime:
        """Calculate start time based on time range"""
        if time_range == TimeRange.LAST_1H:
            return end_time - timedelta(hours=1)
        elif time_range == TimeRange.LAST_6H:
            return end_time - timedelta(hours=6)
        elif time_range == TimeRange.LAST_24H:
            return end_time - timedelta(hours=24)
        elif time_range == TimeRange.LAST_7D:
            return end_time - timedelta(days=7)
        elif time_range == TimeRange.LAST_30D:
            return end_time - timedelta(days=30)
        else:
            return end_time - timedelta(hours=24)  # Default to 24h

    async def _calculate_error_rate(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate error rate for time range"""
        try:
            errors = await self._get_sentry_error_count(start_time, end_time)
            total_requests = await self._get_total_requests(start_time, end_time)

            return (errors / total_requests * 100) if total_requests > 0 else 0
        except Exception:
            return 0.0

    async def _calculate_avg_response_time(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate average response time"""
        try:
            return await self.apm_service.get_avg_response_time(
                start_time=start_time,
                end_time=end_time
            )
        except Exception:
            return 0.0

    async def _calculate_uptime(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> float:
        """Calculate uptime percentage"""
        try:
            # TODO: Implement actual uptime calculation
            return 99.9  # Mock value
        except Exception:
            return 0.0

    # Mock data methods for Sentry integration

    async def _get_sentry_error_trend(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Tuple[datetime, int, int]]:
        """Mock Sentry error trend data"""
        # Return mock data: (timestamp, error_count, total_requests)
        current = start_time
        data = []

        while current <= end_time:
            # Generate mock data with some variation
            error_count = max(0, int(10 + 5 * (0.5 - (current.timestamp() % 86400) / 86400)))
            total_requests = 1000 + int(200 * (0.5 - (current.timestamp() % 86400) / 86400))

            data.append((current, error_count, total_requests))
            current += timedelta(minutes=5)

        return data

    async def _get_sentry_top_errors(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Mock Sentry top errors data"""
        return [
            {"type": "ValidationError", "message": "Invalid input data", "count": 45, "last_seen": "2024-01-15T10:30:00Z"},
            {"type": "TimeoutError", "message": "Database connection timeout", "count": 32, "last_seen": "2024-01-15T10:25:00Z"},
            {"type": "AuthenticationError", "message": "Invalid authentication token", "count": 28, "last_seen": "2024-01-15T10:20:00Z"},
            {"type": "RateLimitError", "message": "API rate limit exceeded", "count": 15, "last_seen": "2024-01-15T10:15:00Z"},
        ]

    async def _get_sentry_error_types(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Mock Sentry error types data"""
        total = 150
        return [
            {"type": "4xx Errors", "count": 60, "percentage": 40.0},
            {"type": "5xx Errors", "count": 30, "percentage": 20.0},
            {"type": "Timeout Errors", "count": 25, "percentage": 16.7},
            {"type": "Validation Errors", "count": 20, "percentage": 13.3},
            {"type": "Other", "count": 15, "percentage": 10.0},
        ]

    async def _get_sentry_recent_errors(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[Dict[str, Any]]:
        """Mock Sentry recent errors data"""
        return [
            {"timestamp": "2024-01-15T10:30:15Z", "level": "error", "type": "ValidationError", "message": "Invalid email format", "environment": "production", "release": "1.2.0"},
            {"timestamp": "2024-01-15T10:28:42Z", "level": "error", "type": "TimeoutError", "message": "Database query timeout", "environment": "production", "release": "1.2.0"},
            {"timestamp": "2024-01-15T10:27:18Z", "level": "warning", "type": "PerformanceWarning", "message": "Slow query detected", "environment": "production", "release": "1.2.0"},
        ]

    async def _get_sentry_error_count(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Mock Sentry error count"""
        return 125  # Mock value

    async def _get_total_requests(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> int:
        """Mock total requests count"""
        return 5000  # Mock value

    # Caching methods

    def _cache_dashboard(self, dashboard: Dashboard) -> None:
        """Cache dashboard data"""
        cache_key = f"dashboard:{dashboard.id}"
        self._dashboard_cache[cache_key] = {
            "dashboard": dashboard,
            "timestamp": datetime.utcnow()
        }

    def _get_cached_dashboard(self, dashboard_id: str) -> Optional[Dashboard]:
        """Get cached dashboard data"""
        cache_key = f"dashboard:{dashboard_id}"
        cached = self._dashboard_cache.get(cache_key)

        if cached and not self._is_cache_expired(dashboard_id):
            return cached["dashboard"]

        return None

    def _is_cache_expired(self, dashboard_id: str) -> bool:
        """Check if dashboard cache is expired"""
        cache_key = f"dashboard:{dashboard_id}"
        cached = self._dashboard_cache.get(cache_key)

        if not cached:
            return True

        age = datetime.utcnow() - cached["timestamp"]
        return age.total_seconds() > self._cache_ttl

    def _clear_cache(self, dashboard_id: str) -> None:
        """Clear cached dashboard data"""
        cache_key = f"dashboard:{dashboard_id}"
        self._dashboard_cache.pop(cache_key, None)

    # Background task management

    async def start_background_refresh(self) -> None:
        """Start background dashboard refresh tasks"""
        if self._running:
            return

        self._running = True

        # Start refresh task for each dashboard
        for dashboard_id in self._builtin_dashboards.keys():
            task = asyncio.create_task(
                self._background_dashboard_refresh(dashboard_id)
            )
            self._refresh_tasks[dashboard_id] = task

        logger.info("Started background dashboard refresh tasks")

    async def stop_background_refresh(self) -> None:
        """Stop background dashboard refresh tasks"""
        self._running = False

        # Cancel all refresh tasks
        for task in self._refresh_tasks.values():
            task.cancel()

        # Wait for tasks to complete
        if self._refresh_tasks:
            await asyncio.gather(*self._refresh_tasks.values(), return_exceptions=True)

        self._refresh_tasks.clear()

        logger.info("Stopped background dashboard refresh tasks")

    async def _background_dashboard_refresh(self, dashboard_id: str) -> None:
        """Background task to refresh dashboard data"""
        while self._running:
            try:
                dashboard = await self.get_dashboard(dashboard_id, refresh_data=True)

                # Calculate sleep time based on dashboard's fastest refresh interval
                min_interval = min(
                    widget.refresh_interval
                    for widget in dashboard.widgets
                )

                # Sleep for the minimum interval, but check if we should stop
                for _ in range(min_interval):
                    if not self._running:
                        break
                    await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background refresh failed for {dashboard_id}: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying


# Export the main service class
__all__ = [
    "DashboardService",
    "Dashboard",
    "DashboardWidget",
    "MetricSeries",
    "DataPoint",
    "DashboardType",
    "TimeRange",
    "ChartType"
]