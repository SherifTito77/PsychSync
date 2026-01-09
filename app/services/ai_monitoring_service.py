"""
AI Engine Monitoring Service
Tracks AI performance, accuracy, and system health metrics
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import time
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of AI metrics to monitor"""

    PROCESSING_TIME = "processing_time"
    ACCURACY_SCORE = "accuracy_score"
    CONFIDENCE_SCORE = "confidence_score"
    ENGAGEMENT_PREDICTION_ACCURACY = "engagement_prediction_accuracy"
    PERSONALIZATION_EFFECTIVENESS = "personalization_effectiveness"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CACHE_HIT_RATE = "cache_hit_rate"


class AlertSeverity(Enum):
    """Severity levels for AI alerts"""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AIMetric:
    """Individual AI metric measurement"""

    metric_type: MetricType
    value: float
    timestamp: datetime
    context: dict[str, Any] = field(default_factory=dict)
    threshold_breach: float | None = None


@dataclass
class AIAlert:
    """AI system alert"""

    alert_id: str
    severity: AlertSeverity
    title: str
    description: str
    metric_type: MetricType
    current_value: float
    threshold_value: float
    timestamp: datetime
    resolution_actions: list[str] = field(default_factory=list)


@dataclass
class AIHealthStatus:
    """Overall AI system health status"""

    overall_status: str  # "healthy", "degraded", "critical"
    health_score: float  # 0.0 to 1.0
    active_alerts: list[AIAlert]
    performance_metrics: dict[str, float]
    last_check: datetime
    uptime_percentage: float
    recommendations: list[str] = field(default_factory=list)


class AIMonitoringService:
    """
    Comprehensive AI engine monitoring service that tracks:
    - Performance metrics and processing times
    - Prediction accuracy and confidence scores
    - System health and error rates
    - Resource utilization and throughput
    - User engagement with AI features
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.metrics_history: list[AIMetric] = []
        self.active_alerts: list[AIAlert] = []
        self.thresholds = self._initialize_thresholds()
        self.monitoring_active = False

    def _initialize_thresholds(self) -> dict[MetricType, dict[str, float]]:
        """Initialize monitoring thresholds for different metrics"""
        return {
            MetricType.PROCESSING_TIME: {
                "warning": 2000,  # 2 seconds
                "critical": 5000,  # 5 seconds
            },
            MetricType.ACCURACY_SCORE: {
                "warning": 0.7,  # 70%
                "critical": 0.5,  # 50%
            },
            MetricType.CONFIDENCE_SCORE: {"warning": 0.6, "critical": 0.4},
            MetricType.ERROR_RATE: {
                "warning": 0.05,  # 5%
                "critical": 0.10,  # 10%
            },
            MetricType.ENGAGEMENT_PREDICTION_ACCURACY: {"warning": 0.65, "critical": 0.5},
            MetricType.PERSONALIZATION_EFFECTIVENESS: {"warning": 0.6, "critical": 0.4},
            MetricType.MEMORY_USAGE: {
                "warning": 0.8,  # 80% of available memory
                "critical": 0.9,  # 90% of available memory
            },
            MetricType.CACHE_HIT_RATE: {
                "warning": 0.7,  # Below 70%
                "critical": 0.5,  # Below 50%
            },
        }

    async def start_monitoring(self) -> None:
        """Start continuous AI engine monitoring"""
        try:
            self.monitoring_active = True
            logger.info("AI Engine monitoring started")

            # Start background monitoring tasks
            asyncio.create_task(self._monitoring_loop())
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._performance_collection_loop())

        except Exception as e:
            logger.error(f"Error starting AI monitoring: {e}")
            self.monitoring_active = False

    async def stop_monitoring(self) -> None:
        """Stop AI engine monitoring"""
        self.monitoring_active = False
        logger.info("AI Engine monitoring stopped")

    async def record_metric(
        self, metric_type: MetricType, value: float, context: dict[str, Any] | None = None
    ) -> None:
        """Record a metric measurement"""
        try:
            metric = AIMetric(
                metric_type=metric_type,
                value=value,
                timestamp=datetime.utcnow(),
                context=context or {},
            )

            # Check for threshold breaches
            threshold_breach = await self._check_threshold_breach(metric)
            if threshold_breach:
                metric.threshold_breach = threshold_breach

            # Store metric
            self.metrics_history.append(metric)

            # Keep only recent metrics (last 24 hours)
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]

            # Trigger alert if threshold breached
            if threshold_breach:
                await self._create_alert(metric)

        except Exception as e:
            logger.error(f"Error recording metric {metric_type.value}: {e}")

    async def get_ai_health_status(self) -> AIHealthStatus:
        """Get comprehensive AI system health status"""
        try:
            # Calculate health score based on recent metrics
            recent_metrics = self._get_recent_metrics(hours=1)

            performance_scores = []
            for metric_type in self.thresholds.keys():
                type_metrics = [m for m in recent_metrics if m.metric_type == metric_type]
                if type_metrics:
                    avg_value = sum(m.value for m in type_metrics) / len(type_metrics)
                    score = self._calculate_health_score(metric_type, avg_value)
                    performance_scores.append(score)

            overall_health_score = (
                sum(performance_scores) / len(performance_scores) if performance_scores else 1.0
            )

            # Determine overall status
            if overall_health_score >= 0.8:
                overall_status = "healthy"
            elif overall_health_score >= 0.6:
                overall_status = "degraded"
            else:
                overall_status = "critical"

            # Calculate performance metrics
            performance_metrics = self._calculate_performance_metrics(recent_metrics)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                recent_metrics, overall_health_score
            )

            return AIHealthStatus(
                overall_status=overall_status,
                health_score=overall_health_score,
                active_alerts=self.active_alerts.copy(),
                performance_metrics=performance_metrics,
                last_check=datetime.utcnow(),
                uptime_percentage=await self._calculate_uptime(),
                recommendations=recommendations,
            )

        except Exception as e:
            logger.error(f"Error getting AI health status: {e}")
            return AIHealthStatus(
                overall_status="unknown",
                health_score=0.0,
                active_alerts=[],
                performance_metrics={},
                last_check=datetime.utcnow(),
                uptime_percentage=0.0,
                recommendations=["Unable to determine system health"],
            )

    async def get_performance_trends(
        self, hours: int = 24, metric_types: list[MetricType] | None = None
    ) -> dict[str, Any]:
        """Get performance trends and analytics"""
        try:
            metrics = self._get_recent_metrics(hours=hours)

            if metric_types:
                metrics = [m for m in metrics if m.metric_type in metric_types]

            trends = {}
            for metric_type in MetricType:
                type_metrics = [m for m in metrics if m.metric_type == metric_type]
                if type_metrics:
                    trends[metric_type.value] = {
                        "current": type_metrics[-1].value if type_metrics else 0,
                        "average": sum(m.value for m in type_metrics) / len(type_metrics),
                        "min": min(m.value for m in type_metrics),
                        "max": max(m.value for m in type_metrics),
                        "trend": self._calculate_trend(type_metrics),
                        "data_points": len(type_metrics),
                    }

            return {
                "time_period_hours": hours,
                "total_metrics": len(metrics),
                "trends": trends,
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error getting performance trends: {e}")
            return {"error": str(e), "trends": {}}

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect basic metrics
                await self._collect_basic_metrics()

                # Check for new alerts
                await self._process_alerts()

                # Sleep for 30 seconds
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _health_check_loop(self) -> None:
        """Periodic health check loop"""
        while self.monitoring_active:
            try:
                health_status = await self.get_ai_health_status()

                # Log health status
                logger.info(
                    f"AI Health Status: {health_status.overall_status} (Score: {health_status.health_score:.2f})"
                )

                # Check for critical issues
                if health_status.overall_status == "critical":
                    await self._handle_critical_health(health_status)

                # Sleep for 5 minutes
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Error in health check loop: {e}")
                await asyncio.sleep(600)

    async def _performance_collection_loop(self) -> None:
        """Collect detailed performance metrics"""
        while self.monitoring_active:
            try:
                # Collect performance metrics
                await self._collect_performance_metrics()

                # Sleep for 10 minutes
                await asyncio.sleep(600)

            except Exception as e:
                logger.error(f"Error in performance collection loop: {e}")
                await asyncio.sleep(600)

    async def _collect_basic_metrics(self) -> None:
        """Collect basic AI engine metrics"""
        try:
            # Simulate metric collection - in real implementation,
            # this would interface with actual AI engine components

            # Processing time metric
            processing_time = 150 + (hash(str(time.time())) % 500)  # Simulated 150-650ms
            await self.record_metric(
                MetricType.PROCESSING_TIME, processing_time, {"component": "ai_processor"}
            )

            # Confidence score metric
            confidence = 0.7 + (hash(str(time.time())) % 30) / 100  # Simulated 0.7-1.0
            await self.record_metric(
                MetricType.CONFIDENCE_SCORE, confidence, {"component": "personality_analyzer"}
            )

            # Error rate metric
            error_occurred = hash(str(time.time())) % 50 == 0  # 2% chance
            error_rate = 0.02 if error_occurred else 0.0
            await self.record_metric(MetricType.ERROR_RATE, error_rate, {"component": "ai_engine"})

        except Exception as e:
            logger.error(f"Error collecting basic metrics: {e}")

    async def _collect_performance_metrics(self) -> None:
        """Collect detailed performance metrics"""
        try:
            # Memory usage simulation
            memory_usage = 0.6 + (hash(str(time.time())) % 30) / 100  # 60-90%
            await self.record_metric(
                MetricType.MEMORY_USAGE, memory_usage, {"component": "ai_engine"}
            )

            # Throughput simulation
            throughput = 50 + (hash(str(time.time())) % 100)  # 50-150 requests/minute
            await self.record_metric(MetricType.THROUGHPUT, throughput, {"component": "ai_api"})

            # Cache hit rate simulation
            cache_hit_rate = 0.8 + (hash(str(time.time())) % 20) / 100  # 80-100%
            await self.record_metric(
                MetricType.CACHE_HIT_RATE, cache_hit_rate, {"component": "ai_cache"}
            )

        except Exception as e:
            logger.error(f"Error collecting performance metrics: {e}")

    async def _check_threshold_breach(self, metric: AIMetric) -> float | None:
        """Check if metric breaches any thresholds"""
        try:
            if metric.metric_type not in self.thresholds:
                return None

            thresholds = self.thresholds[metric.metric_type]

            if metric.value >= thresholds.get("critical", float("inf")):
                return thresholds["critical"]
            if metric.value >= thresholds.get("warning", float("inf")):
                return thresholds["warning"]
            if metric.value <= thresholds.get("critical_low", float("-inf")):
                return thresholds["critical_low"]
            if metric.value <= thresholds.get("warning_low", float("-inf")):
                return thresholds["warning_low"]

            return None

        except Exception as e:
            logger.error(f"Error checking threshold breach: {e}")
            return None

    async def _create_alert(self, metric: AIMetric) -> None:
        """Create an alert for threshold breach"""
        try:
            alert_id = f"{metric.metric_type.value}_{int(time.time())}"

            severity = AlertSeverity.WARNING
            if metric.metric_type in self.thresholds:
                thresholds = self.thresholds[metric.metric_type]
                if metric.threshold_breach == thresholds.get("critical", 0):
                    severity = AlertSeverity.CRITICAL
                elif metric.threshold_breach == thresholds.get("warning", 0):
                    severity = AlertSeverity.WARNING

            alert = AIAlert(
                alert_id=alert_id,
                severity=severity,
                title=f"{metric.metric_type.value.replace('_', ' ').title()} Threshold Breach",
                description=f"Metric {metric.metric_type.value} has exceeded threshold with value {metric.value:.3f}",
                metric_type=metric.metric_type,
                current_value=metric.value,
                threshold_value=metric.threshold_breach or 0,
                timestamp=datetime.utcnow(),
                resolution_actions=await self._get_resolution_actions(metric),
            )

            self.active_alerts.append(alert)

            # Log alert
            logger.warning(f"AI Alert: {alert.title} - {alert.description}")

            # Keep only last 100 active alerts
            if len(self.active_alerts) > 100:
                self.active_alerts = self.active_alerts[-100:]

        except Exception as e:
            logger.error(f"Error creating alert: {e}")

    def _get_recent_metrics(self, hours: int = 1) -> list[AIMetric]:
        """Get metrics from recent hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return [m for m in self.metrics_history if m.timestamp > cutoff_time]

    def _calculate_health_score(self, metric_type: MetricType, value: float) -> float:
        """Calculate health score for a metric (0.0 to 1.0)"""
        try:
            if metric_type not in self.thresholds:
                return 1.0

            thresholds = self.thresholds[metric_type]

            # For metrics where higher is better (accuracy, confidence, etc.)
            if metric_type in [
                MetricType.ACCURACY_SCORE,
                MetricType.CONFIDENCE_SCORE,
                MetricType.ENGAGEMENT_PREDICTION_ACCURACY,
                MetricType.PERSONALIZATION_EFFECTIVENESS,
                MetricType.CACHE_HIT_RATE,
            ]:
                if value >= 0.8:
                    return 1.0
                if value >= 0.6:
                    return 0.8
                if value >= thresholds.get("critical", 0.5):
                    return 0.6
                return 0.3

            # For metrics where lower is better (processing time, error rate, etc.)
            if metric_type == MetricType.PROCESSING_TIME:
                if value <= 1000:  # 1 second
                    return 1.0
                if value <= 2000:  # 2 seconds
                    return 0.8
                if value <= thresholds.get("warning", 2000):
                    return 0.6
                return 0.3

            if metric_type == MetricType.ERROR_RATE:
                if value <= 0.01:  # 1%
                    return 1.0
                if value <= 0.05:  # 5%
                    return 0.8
                if value <= thresholds.get("warning", 0.05):
                    return 0.6
                return 0.3

            return 0.7  # Default medium score

        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 0.5

    def _calculate_performance_metrics(self, metrics: list[AIMetric]) -> dict[str, float]:
        """Calculate overall performance metrics"""
        performance = {}

        for metric_type in MetricType:
            type_metrics = [m for m in metrics if m.metric_type == metric_type]
            if type_metrics:
                avg_value = sum(m.value for m in type_metrics) / len(type_metrics)
                performance[metric_type.value] = avg_value

        return performance

    async def _generate_recommendations(
        self, metrics: list[AIMetric], health_score: float
    ) -> list[str]:
        """Generate improvement recommendations based on metrics"""
        recommendations = []

        try:
            # Analyze specific metrics
            for metric_type in MetricType:
                type_metrics = [m for m in metrics if m.metric_type == metric_type]
                if type_metrics:
                    avg_value = sum(m.value for m in type_metrics) / len(type_metrics)

                    if metric_type == MetricType.PROCESSING_TIME and avg_value > 2000:
                        recommendations.append(
                            "Consider optimizing AI algorithms for faster processing"
                        )
                    elif metric_type == MetricType.ACCURACY_SCORE and avg_value < 0.7:
                        recommendations.append("Review AI model training data and parameters")
                    elif metric_type == MetricType.ERROR_RATE and avg_value > 0.05:
                        recommendations.append("Investigate and fix frequent AI processing errors")
                    elif metric_type == MetricType.MEMORY_USAGE and avg_value > 0.8:
                        recommendations.append(
                            "Optimize AI memory usage or allocate more resources"
                        )
                    elif metric_type == MetricType.CACHE_HIT_RATE and avg_value < 0.7:
                        recommendations.append("Improve AI model caching strategy")

            # General recommendations based on health score
            if health_score < 0.6:
                recommendations.append("System health is degraded - consider immediate attention")
            elif health_score < 0.8:
                recommendations.append("Monitor system performance and consider optimizations")

            return recommendations[:5]  # Limit to top 5 recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return ["Unable to generate recommendations due to monitoring error"]

    def _calculate_trend(self, metrics: list[AIMetric]) -> str:
        """Calculate trend direction for a metric"""
        if len(metrics) < 2:
            return "insufficient_data"

        # Compare last 10% with previous 10%
        split_point = max(len(metrics) // 10, 2)
        recent_avg = sum(m.value for m in metrics[-split_point:]) / split_point
        previous_avg = sum(m.value for m in metrics[-split_point * 2 : -split_point]) / split_point

        if recent_avg > previous_avg * 1.05:
            return "improving"
        if recent_avg < previous_avg * 0.95:
            return "declining"
        return "stable"

    async def _get_resolution_actions(self, metric: AIMetric) -> list[str]:
        """Get recommended resolution actions for a metric alert"""
        actions = []

        if metric.metric_type == MetricType.PROCESSING_TIME:
            actions = [
                "Check AI model optimization settings",
                "Review computational resource allocation",
                "Consider model quantization or pruning",
            ]
        elif metric.metric_type == MetricType.ERROR_RATE:
            actions = [
                "Review AI input validation",
                "Check for model corruption",
                "Monitor system logs for error patterns",
            ]
        elif metric.metric_type == MetricType.MEMORY_USAGE:
            actions = [
                "Implement memory cleanup procedures",
                "Review memory leak in AI components",
                "Consider increasing system memory",
            ]
        else:
            actions = [
                "Monitor metric trend",
                "Review recent system changes",
                "Check for external factors affecting performance",
            ]

        return actions

    async def _calculate_uptime(self) -> float:
        """Calculate AI engine uptime percentage"""
        # Simplified implementation - would track actual uptime in production
        return 0.98  # 98% uptime

    async def _process_alerts(self) -> None:
        """Process and manage active alerts"""
        try:
            # Auto-resolve old alerts
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            self.active_alerts = [
                alert for alert in self.active_alerts if alert.timestamp > cutoff_time
            ]

        except Exception as e:
            logger.error(f"Error processing alerts: {e}")

    async def _handle_critical_health(self, health_status: AIHealthStatus) -> None:
        """Handle critical health situations"""
        try:
            # Log critical situation
            logger.error(
                f"CRITICAL: AI Engine health is critical - Score: {health_status.health_score:.2f}"
            )

            # In a real implementation, this would trigger:
            # - Notification to administrators
            # - Automatic failover procedures
            # - Emergency diagnostics
            # - Service degradation protocols

        except Exception as e:
            logger.error(f"Error handling critical health: {e}")
