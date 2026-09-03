"""
Advanced Trend Reporting Service

Transforms statistical analysis into actionable insights and recommendations.
Generates comprehensive reports with executive summaries and detailed analytics.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.db.models.longitudinal_analysis import ChangeDetectionEvent
from app.services.change_detection import AdvancedChangeDetector
from app.services.longitudinal_analysis import LongitudinalAnalyzer, TrendDirection

logger = logging.getLogger(__name__)


class SeverityLevel(Enum):
    """Severity levels for identified issues and opportunities"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class InsightCategory(Enum):
    """Categories for different types of insights"""

    PERFORMANCE_TREND = "performance_trend"
    BEHAVIORAL_CHANGE = "behavioral_change"
    ANOMALY_DETECTION = "anomaly_detection"
    GROWTH_OPPORTUNITY = "growth_opportunity"
    RISK_ASSESSMENT = "risk_assessment"
    COMPARATIVE_ANALYSIS = "comparative_analysis"
    PREDICTIVE_INSIGHT = "predictive_insight"


@dataclass
class Insight:
    """Single insight with recommendation"""

    category: InsightCategory
    severity: SeverityLevel
    title: str
    description: str
    metric_name: str
    current_value: float
    previous_value: float | None
    percent_change: float | None
    recommendation: str
    confidence_score: float
    timeframe: str
    supporting_data: dict[str, Any]


@dataclass
class ExecutiveSummary:
    """Executive summary for trend analysis report"""

    overall_score: float
    key_highlights: list[str]
    critical_issues: list[str]
    growth_opportunities: list[str]
    predictive_insights: list[str]
    data_quality_score: float
    analysis_period: str
    user_count: int


@dataclass
class DetailedStatistics:
    """Detailed statistical analysis"""

    trend_analysis: dict[str, Any]
    change_point_analysis: dict[str, Any]
    seasonal_patterns: dict[str, Any]
    correlation_analysis: dict[str, Any]
    predictive_confidence: dict[str, Any]


@dataclass
class TrendReport:
    """Complete trend analysis report"""

    executive_summary: ExecutiveSummary
    insights: list[Insight]
    detailed_statistics: DetailedStatistics
    charts_data: dict[str, Any]
    recommendations: list[str]
    metadata: dict[str, Any]


class TrendReportingService:
    """Advanced trend reporting and insights generation"""

    def __init__(self, db_session: Session):
        self.db = db_session
        self.longitudinal_analyzer = LongitudinalAnalyzer(db_session)
        self.change_detector = AdvancedChangeDetector(db_session)
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def generate_comprehensive_report(
        self,
        user_id: str | None = None,
        team_id: str | None = None,
        organization_id: str | None = None,
        start_date: datetime = None,
        end_date: datetime = None,
        metrics: list[str] | None = None,
    ) -> TrendReport:
        """Generate comprehensive trend analysis report"""

        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        self.logger.info(
            f"Generating comprehensive trend report for user: {user_id}, team: {team_id}"
        )

        # Generate all analysis components
        executive_summary = await self._generate_executive_summary(
            user_id, team_id, organization_id, start_date, end_date, metrics
        )

        insights = await self._generate_insights(
            user_id, team_id, organization_id, start_date, end_date, metrics
        )

        detailed_statistics = await self._generate_detailed_statistics(
            user_id, team_id, organization_id, start_date, end_date, metrics
        )

        charts_data = await self._prepare_charts_data(
            user_id, team_id, organization_id, start_date, end_date, metrics
        )

        recommendations = await self._generate_strategic_recommendations(
            insights, detailed_statistics
        )

        metadata = {
            "generated_at": datetime.utcnow().isoformat(),
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": (end_date - start_date).days,
            },
            "scope": {
                "user_id": user_id,
                "team_id": team_id,
                "organization_id": organization_id,
                "metrics": metrics or ["all"],
            },
            "data_points_count": await self._count_data_points(
                user_id, team_id, organization_id, start_date, end_date
            ),
        }

        return TrendReport(
            executive_summary=executive_summary,
            insights=insights,
            detailed_statistics=detailed_statistics,
            charts_data=charts_data,
            recommendations=recommendations,
            metadata=metadata,
        )

    async def _generate_executive_summary(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None,
    ) -> ExecutiveSummary:
        """Generate executive summary with key findings"""

        # Get trend analysis for key metrics
        key_metrics = metrics or [
            "engagement",
            "performance",
            "wellness",
            "collaboration",
        ]
        trend_results = []

        for metric in key_metrics:
            try:
                trend_data = await self.longitudinal_analyzer.aggregate_time_series(
                    user_id=user_id,
                    team_id=team_id,
                    metric_name=metric,
                    start_date=start_date,
                    end_date=end_date,
                    bucket_size="week",
                )

                if trend_data.data_points:
                    trend_analysis = await self.longitudinal_analyzer.analyze_trend(
                        user_id=user_id,
                        team_id=team_id,
                        metric_name=metric,
                        start_date=start_date,
                        end_date=end_date,
                    )
                    trend_results.append((metric, trend_analysis))

            except Exception as e:
                self.logger.warning(f"Failed to analyze trend for {metric}: {e}")

        # Calculate overall score based on trend directions and magnitudes
        overall_score = self._calculate_overall_score(trend_results)

        # Generate key highlights
        key_highlights = []
        critical_issues = []
        growth_opportunities = []
        predictive_insights = []

        for metric, trend_analysis in trend_results:
            if trend_analysis.trend_direction == TrendDirection.IMPROVING:
                if trend_analysis.strength > 0.7:
                    key_highlights.append(
                        f"Strong improvement in {metric}: +{trend_analysis.strength:.1%}"
                    )
                else:
                    key_highlights.append(
                        f"Positive trend in {metric}: +{trend_analysis.strength:.1%}"
                    )
            elif trend_analysis.trend_direction == TrendDirection.DECLINING:
                if trend_analysis.strength > 0.7:
                    critical_issues.append(
                        f"Significant decline in {metric}: -{trend_analysis.strength:.1%}"
                    )
                else:
                    critical_issues.append(
                        f"Negative trend in {metric}: -{trend_analysis.strength:.1%}"
                    )

            # Predictive insights based on trend strength and consistency
            if trend_analysis.strength > 0.8:
                if trend_analysis.trend_direction == TrendDirection.IMPROVING:
                    predictive_insights.append(
                        f"Continued {metric} improvement expected"
                    )
                else:
                    predictive_insights.append(f"{metric} decline likely to continue")

        # Get user count for scope
        user_count = await self._count_users(user_id, team_id, organization_id)

        # Assess data quality
        data_quality_score = await self._assess_data_quality(
            user_id, team_id, organization_id, start_date, end_date
        )

        return ExecutiveSummary(
            overall_score=overall_score,
            key_highlights=key_highlights[:5],  # Top 5 highlights
            critical_issues=critical_issues[:5],  # Top 5 issues
            growth_opportunities=growth_opportunities[:5],
            predictive_insights=predictive_insights[:5],
            data_quality_score=data_quality_score,
            analysis_period=f"{start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}",
            user_count=user_count,
        )

    async def _generate_insights(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None,
    ) -> list[Insight]:
        """Generate detailed insights across different categories"""

        insights = []

        # Performance trend insights
        insights.extend(
            await self._generate_performance_trend_insights(
                user_id, team_id, start_date, end_date, metrics
            )
        )

        # Behavioral change insights
        insights.extend(
            await self._generate_behavioral_change_insights(
                user_id, team_id, start_date, end_date
            )
        )

        # Anomaly detection insights
        insights.extend(
            await self._generate_anomaly_insights(
                user_id, team_id, start_date, end_date
            )
        )

        # Growth opportunity insights
        insights.extend(
            await self._generate_growth_opportunity_insights(
                user_id, team_id, start_date, end_date
            )
        )

        # Risk assessment insights
        insights.extend(
            await self._generate_risk_assessment_insights(
                user_id, team_id, start_date, end_date
            )
        )

        # Comparative analysis insights
        insights.extend(
            await self._generate_comparative_insights(
                user_id, team_id, organization_id, start_date, end_date
            )
        )

        # Predictive insights
        insights.extend(
            await self._generate_predictive_insights(
                user_id, team_id, start_date, end_date, metrics
            )
        )

        # Sort insights by severity and confidence
        insights.sort(
            key=lambda x: (list(SeverityLevel).index(x.severity), -x.confidence_score)
        )

        return insights[:20]  # Top 20 insights

    async def _generate_performance_trend_insights(
        self,
        user_id: str | None,
        team_id: str | None,
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None,
    ) -> list[Insight]:
        """Generate insights based on performance trends"""

        insights = []
        performance_metrics = [
            "productivity",
            "quality",
            "efficiency",
            "goal_completion",
        ]

        for metric in performance_metrics:
            if metrics and metric not in metrics:
                continue

            try:
                trend_analysis = await self.longitudinal_analyzer.analyze_trend(
                    user_id=user_id,
                    team_id=team_id,
                    metric_name=metric,
                    start_date=start_date,
                    end_date=end_date,
                )

                if trend_analysis.trend_direction != TrendDirection.STABLE:
                    severity = self._calculate_trend_severity(
                        trend_analysis.strength, trend_analysis.trend_direction
                    )
                    category = InsightCategory.PERFORMANCE_TREND

                    insight = Insight(
                        category=category,
                        severity=severity,
                        title=f"{metric.replace('_', ' ').title()} Trend Analysis",
                        description=self._generate_trend_description(
                            metric, trend_analysis
                        ),
                        metric_name=metric,
                        current_value=trend_analysis.final_value or 0,
                        previous_value=trend_analysis.initial_value,
                        percent_change=trend_analysis.percent_change,
                        recommendation=self._generate_trend_recommendation(
                            metric, trend_analysis
                        ),
                        confidence_score=trend_analysis.trend_confidence,
                        timeframe="last 90 days",
                        supporting_data={
                            "trend_direction": trend_analysis.trend_direction.value,
                            "trend_strength": trend_analysis.strength,
                            "statistical_significance": trend_analysis.trend_confidence
                            > 0.95,
                            "data_points": (
                                len(trend_analysis.data_points)
                                if trend_analysis.data_points
                                else 0
                            ),
                        },
                    )
                    insights.append(insight)

            except Exception as e:
                self.logger.warning(
                    f"Failed to generate performance trend insight for {metric}: {e}"
                )

        return insights

    async def _generate_behavioral_change_insights(
        self,
        user_id: str | None,
        team_id: str | None,
        start_date: datetime,
        end_date: datetime,
    ) -> list[Insight]:
        """Generate insights based on detected behavioral changes"""

        insights = []

        try:
            # Get recent change detection events
            change_events = (
                self.db.query(ChangeDetectionEvent)
                .filter(
                    ChangeDetectionEvent.user_id == user_id if user_id else True,
                    ChangeDetectionEvent.team_id == team_id if team_id else True,
                    ChangeDetectionEvent.change_date >= start_date,
                    ChangeDetectionEvent.confidence >= 0.7,
                )
                .order_by(desc(ChangeDetectionEvent.change_date))
                .limit(10)
                .all()
            )

            for event in change_events:
                severity = (
                    SeverityLevel.HIGH
                    if event.magnitude > 0.5
                    else SeverityLevel.MEDIUM
                )
                if event.magnitude > 0.8:
                    severity = SeverityLevel.CRITICAL

                insight = Insight(
                    category=InsightCategory.BEHAVIORAL_CHANGE,
                    severity=severity,
                    title=f"Behavioral Change Detected: {event.metric_name}",
                    description=f"Significant {event.change_type} detected in {event.metric_name} on {event.change_date.strftime('%b %d')}. Change magnitude: {event.magnitude:.2f}",
                    metric_name=event.metric_name,
                    current_value=event.post_change_mean,
                    previous_value=event.pre_change_mean,
                    percent_change=event.magnitude * 100,
                    recommendation=self._generate_change_recommendation(event),
                    confidence_score=float(event.confidence),
                    timeframe=f"since {event.change_date.strftime('%b %d')}",
                    supporting_data={
                        "change_type": event.change_type,
                        "detection_method": event.detection_method,
                        "change_date": event.change_date.isoformat(),
                        "algorithm_details": event.algorithm_details or {},
                    },
                )
                insights.append(insight)

        except Exception as e:
            self.logger.warning(f"Failed to generate behavioral change insights: {e}")

        return insights

    async def _generate_detailed_statistics(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None,
    ) -> DetailedStatistics:
        """Generate detailed statistical analysis"""

        # Trend analysis statistics
        trend_analysis_stats = await self._analyze_trend_statistics(
            user_id, team_id, start_date, end_date, metrics
        )

        # Change point analysis
        change_point_stats = await self._analyze_change_point_statistics(
            user_id, team_id, start_date, end_date
        )

        # Seasonal patterns
        seasonal_patterns = await self._analyze_seasonal_patterns(
            user_id, team_id, start_date, end_date
        )

        # Correlation analysis
        correlation_analysis = await self._analyze_metric_correlations(
            user_id, team_id, start_date, end_date, metrics
        )

        # Predictive confidence
        predictive_confidence = await self._analyze_predictive_confidence(
            user_id, team_id, start_date, end_date, metrics
        )

        return DetailedStatistics(
            trend_analysis=trend_analysis_stats,
            change_point_analysis=change_point_stats,
            seasonal_patterns=seasonal_patterns,
            correlation_analysis=correlation_analysis,
            predictive_confidence=predictive_confidence,
        )

    async def _prepare_charts_data(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
        metrics: list[str] | None,
    ) -> dict[str, Any]:
        """Prepare data for visualization charts"""

        charts_data = {}

        # Time series data for line charts
        charts_data["time_series"] = await self._get_time_series_chart_data(
            user_id, team_id, start_date, end_date, metrics
        )

        # Change point visualization data
        charts_data["change_points"] = await self._get_change_point_chart_data(
            user_id, team_id, start_date, end_date
        )

        # Trend comparison data
        charts_data["trend_comparison"] = await self._get_trend_comparison_data(
            user_id, team_id, start_date, end_date, metrics
        )

        # Distribution data
        charts_data["distributions"] = await self._get_distribution_data(
            user_id, team_id, start_date, end_date, metrics
        )

        # Correlation heatmap data
        charts_data["correlations"] = await self._get_correlation_heatmap_data(
            user_id, team_id, start_date, end_date, metrics
        )

        return charts_data

    async def _generate_strategic_recommendations(
        self, insights: list[Insight], detailed_stats: DetailedStatistics
    ) -> list[str]:
        """Generate strategic recommendations based on insights"""

        recommendations = []

        # Analyze insights for patterns
        critical_issues = [
            i
            for i in insights
            if i.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]
        ]
        performance_trends = [
            i for i in insights if i.category == InsightCategory.PERFORMANCE_TREND
        ]
        growth_opportunities = [
            i for i in insights if i.category == InsightCategory.GROWTH_OPPORTUNITY
        ]

        # Critical issue recommendations
        if critical_issues:
            recommendations.append(
                f"URGENT: Address {len(critical_issues)} critical behavioral issues "
                f"that are impacting performance and wellbeing"
            )

        # Performance trend recommendations
        declining_trends = [
            t for t in performance_trends if t.percent_change and t.percent_change < -10
        ]
        if declining_trends:
            recommendations.append(
                f"Implement targeted interventions for {len(declining_trends)} declining "
                f"performance metrics showing >10% decrease"
            )

        # Growth opportunity recommendations
        if growth_opportunities:
            recommendations.append(
                f"Capitalize on {len(growth_opportunities)} identified growth opportunities "
                f"to maximize team potential"
            )

        # Predictive recommendations
        if (
            detailed_stats.predictive_confidence.get("high_confidence_predictions", 0)
            > 5
        ):
            recommendations.append(
                "Leverage high-confidence predictive insights to proactively manage "
                "future challenges and opportunities"
            )

        # Correlation-based recommendations
        strong_correlations = detailed_stats.correlation_analysis.get(
            "strong_correlations", []
        )
        if strong_correlations:
            recommendations.append(
                f"Focus on key behavioral drivers identified through {len(strong_correlations)} "
                f"strong metric correlations"
            )

        # Data quality recommendations
        data_quality = detailed_stats.trend_analysis.get("data_quality_score", 1.0)
        if data_quality < 0.8:
            recommendations.append(
                "Improve data collection consistency to increase confidence in insights "
                f"(current quality: {data_quality:.1%})"
            )

        return recommendations[:10]  # Top 10 recommendations

    # Helper methods
    def _calculate_overall_score(self, trend_results: list[tuple[str, Any]]) -> float:
        """Calculate overall performance score from trend analysis"""
        if not trend_results:
            return 0.5  # Neutral score

        total_score = 0
        total_weight = 0

        for metric, trend_analysis in trend_results:
            # Convert trend direction to score (-1 to 1)
            direction_score = {
                TrendDirection.IMPROVING: 1,
                TrendDirection.STABLE: 0,
                TrendDirection.DECLINING: -1,
                TrendDirection.UNKNOWN: 0,
            }.get(trend_analysis.trend_direction, 0)

            # Weight by trend strength and confidence
            weight = trend_analysis.strength * trend_analysis.trend_confidence
            score = direction_score * weight

            total_score += score
            total_weight += weight

        return (
            max(0, min(1, (total_score / total_weight + 1) / 2))
            if total_weight > 0
            else 0.5
        )

    def _calculate_trend_severity(
        self, strength: float, direction: TrendDirection
    ) -> SeverityLevel:
        """Calculate severity level based on trend strength and direction"""
        if direction == TrendDirection.DECLINING:
            if strength > 0.8:
                return SeverityLevel.CRITICAL
            if strength > 0.6:
                return SeverityLevel.HIGH
            if strength > 0.4:
                return SeverityLevel.MEDIUM
            return SeverityLevel.LOW
        if strength > 0.7:
            return SeverityLevel.LOW  # Good improvement
        if strength > 0.4:
            return SeverityLevel.MEDIUM
        return SeverityLevel.INFO

    def _generate_trend_description(self, metric: str, trend_analysis: Any) -> str:
        """Generate human-readable trend description"""
        direction = trend_analysis.trend_direction.value.lower()
        strength = trend_analysis.strength

        if direction == "improving":
            if strength > 0.7:
                return f"Exceptional improvement in {metric.replace('_', ' ')} with strong positive momentum"
            if strength > 0.4:
                return f"Solid improvement in {metric.replace('_', ' ')} showing consistent positive progress"
            return f"Mild improvement in {metric.replace('_', ' ')} with gradual positive trend"
        if direction == "declining":
            if strength > 0.7:
                return f"Significant decline in {metric.replace('_', ' ')} requiring immediate attention"
            if strength > 0.4:
                return f"Concerning decline in {metric.replace('_', ' ')} that needs intervention"
            return f"Slight decline in {metric.replace('_', ' ')} worth monitoring"
        return f"{metric.replace('_', ' ')} remains stable with no significant trend"

    def _generate_trend_recommendation(self, metric: str, trend_analysis: Any) -> str:
        """Generate recommendation based on trend analysis"""
        direction = trend_analysis.trend_direction
        strength = trend_analysis.strength

        if direction == TrendDirection.IMPROVING:
            if strength > 0.7:
                return f"Maintain current strategies that are driving exceptional {metric} performance"
            return f"Continue positive momentum by reinforcing successful {metric} practices"
        if direction == TrendDirection.DECLINING:
            if strength > 0.7:
                return f"Immediate intervention required: conduct root cause analysis for {metric} decline"
            return f"Monitor {metric} closely and implement corrective measures"
        return f"Continue monitoring {metric} and explore optimization opportunities"

    def _generate_change_recommendation(self, event: ChangeDetectionEvent) -> str:
        """Generate recommendation based on change detection event"""
        if event.change_type == "increase":
            return f"Investigate factors driving the increase in {event.metric_name} and leverage positive drivers"
        if event.change_type == "decrease":
            return f"Address root causes of {event.metric_name} decrease and implement recovery plan"
        if event.change_type == "variance_change":
            return f"Review {event.metric_name} stability and implement consistency measures"
        return f"Further investigate the {event.change_type} in {event.metric_name}"

    # Additional helper methods for data analysis
    async def _count_users(
        self, user_id: str | None, team_id: str | None, organization_id: str | None
    ) -> int:
        """Count users in the analysis scope"""
        # This is a simplified implementation
        # In practice, you'd query your user/team/organization tables
        return 1 if user_id else (10 if team_id else (100 if organization_id else 1))

    async def _assess_data_quality(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Assess quality of data for analysis"""
        # This would check data completeness, consistency, and accuracy
        # Simplified implementation returns a high quality score
        return 0.92

    async def _count_data_points(
        self,
        user_id: str | None,
        team_id: str | None,
        organization_id: str | None,
        start_date: datetime,
        end_date: datetime,
    ) -> int:
        """Count total data points in analysis"""
        # Simplified implementation
        return 500

    # Placeholder methods for detailed analysis components
    async def _analyze_trend_statistics(self, *args, **kwargs) -> dict[str, Any]:
        return {"data_quality_score": 0.92, "trend_count": 15}

    async def _analyze_change_point_statistics(self, *args, **kwargs) -> dict[str, Any]:
        return {"change_points_detected": 8, "significant_changes": 3}

    async def _analyze_seasonal_patterns(self, *args, **kwargs) -> dict[str, Any]:
        return {"seasonal_strength": 0.3, "peak_periods": ["monday", "friday"]}

    async def _analyze_metric_correlations(self, *args, **kwargs) -> dict[str, Any]:
        return {"strong_correlations": 5, "avg_correlation": 0.42}

    async def _analyze_predictive_confidence(self, *args, **kwargs) -> dict[str, Any]:
        return {"high_confidence_predictions": 12, "avg_confidence": 0.78}

    async def _get_time_series_chart_data(self, *args, **kwargs) -> dict[str, Any]:
        return {"datasets": [], "labels": []}

    async def _get_change_point_chart_data(self, *args, **kwargs) -> dict[str, Any]:
        return {"change_points": [], "baseline": []}

    async def _get_trend_comparison_data(self, *args, **kwargs) -> dict[str, Any]:
        return {"metrics": [], "trends": []}

    async def _get_distribution_data(self, *args, **kwargs) -> dict[str, Any]:
        return {"distributions": []}

    async def _get_correlation_heatmap_data(self, *args, **kwargs) -> dict[str, Any]:
        return {"correlation_matrix": []}

    # Additional insight generation methods (simplified implementations)
    async def _generate_anomaly_insights(self, *args, **kwargs) -> list[Insight]:
        return []

    async def _generate_growth_opportunity_insights(
        self, *args, **kwargs
    ) -> list[Insight]:
        return []

    async def _generate_risk_assessment_insights(
        self, *args, **kwargs
    ) -> list[Insight]:
        return []

    async def _generate_comparative_insights(self, *args, **kwargs) -> list[Insight]:
        return []

    async def _generate_predictive_insights(self, *args, **kwargs) -> list[Insight]:
        return []
