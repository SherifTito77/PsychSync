"""
Longitudinal Trend Analysis for Radar System
Analyzes historical patterns, change points, and long-term trends
"""

import logging
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.toxicity_detection import ToxicityLevel, ToxicityPattern

logger = logging.getLogger(__name__)


@dataclass
class TrendDataPoint:
    """Single data point in trend analysis"""

    date: datetime
    value: float
    zone: str
    metadata: Dict[str, Any] = None


@dataclass
class ChangePoint:
    """Detected change point in trends"""

    date: datetime
    change_type: str  # 'increase', 'decrease', 'spike', 'drop'
    magnitude: float
    confidence: float
    context: Dict[str, Any]


@dataclass
class SeasonalPattern:
    """Detected seasonal pattern"""

    pattern_type: str  # 'weekly', 'monthly', 'quarterly'
    period: str
    average_value: float
    peak_times: List[str]
    trough_times: List[str]


class LongitudinalTrendAnalyzer:
    """
    Longitudinal trend analysis with change point detection

    Features:
    - Long-term trend analysis (30/60/90/180/365 days)
    - Change point detection (sudden shifts)
    - Seasonal pattern detection
    - Comparative analysis (period-over-period)
    - Forecasting with confidence intervals
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_longitudinal_trends(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str] = None,
        days_back: int = 90,
    ) -> Dict[str, Any]:
        """
        Comprehensive longitudinal trend analysis

        Returns:
            - Trend direction and velocity
            - Change points
            - Seasonal patterns
            - Forecasts
            - Comparative metrics
        """
        try:
            # Get historical data
            historical_data = await self._get_historical_data(
                db, organization_id, team_id, days_back
            )

            if not historical_data:
                return {
                    "error": "insufficient_data",
                    "message": f"Not enough data for {days_back}-day analysis",
                }

            # Convert to trend data points
            trend_points = self._convert_to_trend_points(historical_data)

            # Analyze trends
            trend_analysis = self._calculate_trend_metrics(trend_points)

            # Detect change points
            change_points = self._detect_change_points(trend_points)

            # Detect seasonal patterns
            seasonal_patterns = self._detect_seasonal_patterns(trend_points)

            # Calculate comparative metrics
            comparative_metrics = await self._calculate_comparative_metrics(
                trend_points, days_back
            )

            # Generate forecast
            forecast = self._generate_forecast(trend_points)

            return {
                "analysis_period": f"{days_back} days",
                "data_points": len(trend_points),
                "trend_analysis": trend_analysis,
                "change_points": [
                    self._serialize_change_point(cp) for cp in change_points
                ],
                "seasonal_patterns": [
                    self._serialize_seasonal(sp) for sp in seasonal_patterns
                ],
                "comparative_metrics": comparative_metrics,
                "forecast": forecast,
                "analyzed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Longitudinal analysis failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "message": "Failed to analyze longitudinal trends",
            }

    async def _get_historical_data(
        self,
        db: AsyncSession,
        organization_id: str,
        team_id: Optional[str],
        days_back: int,
    ) -> List[ToxicityPattern]:
        """Get historical toxicity pattern data"""
        cutoff_date = datetime.utcnow().date() - timedelta(days=days_back)

        query = select(ToxicityPattern).filter(
            and_(
                ToxicityPattern.organization_id == organization_id,
                ToxicityPattern.detection_date >= cutoff_date,
            )
        )

        if team_id:
            query = query.filter(ToxicityPattern.team_id == team_id)

        query = query.order_by(ToxicityPattern.detection_date.asc())

        result = await db.execute(query)
        return result.scalars().all()

    def _convert_to_trend_points(
        self, patterns: List[ToxicityPattern]
    ) -> List[TrendDataPoint]:
        """Convert patterns to trend data points"""
        # Group by date and calculate daily aggregates
        daily_data = defaultdict(lambda: {"count": 0, "severity_sum": 0.0})

        for pattern in patterns:
            date_key = pattern.detection_date
            severity = self._severity_to_float(pattern.severity_level)

            daily_data[date_key]["count"] += 1
            daily_data[date_key]["severity_sum"] += severity

        # Convert to trend points
        trend_points = []
        for date_str, data in sorted(daily_data.items()):
            avg_severity = (
                data["severity_sum"] / data["count"] if data["count"] > 0 else 0
            )
            trend_points.append(
                TrendDataPoint(
                    date=datetime.combine(date_str, datetime.min.time()),
                    value=avg_severity,
                    zone=self._severity_to_zone(avg_severity),
                    metadata={"pattern_count": data["count"]},
                )
            )

        return trend_points

    def _calculate_trend_metrics(self, points: List[TrendDataPoint]) -> Dict[str, Any]:
        """Calculate comprehensive trend metrics"""
        if len(points) < 2:
            return {"trend": "insufficient_data"}

        values = [p.value for p in points]

        # Calculate linear regression
        x = list(range(len(values)))
        n = len(values)

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi**2 for xi in x)

        # Slope (trend velocity)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)

        # Current vs baseline
        current_value = values[-1]
        baseline_value = values[0]
        pct_change = (
            ((current_value - baseline_value) / baseline_value * 100)
            if baseline_value > 0
            else 0
        )

        # Volatility (standard deviation)
        volatility = statistics.stdev(values) if len(values) > 1 else 0

        # Trend classification
        if slope > 0.01:
            trend_direction = "increasing"
        elif slope < -0.01:
            trend_direction = "decreasing"
        else:
            trend_direction = "stable"

        return {
            "trend_direction": trend_direction,
            "trend_velocity": round(slope, 4),
            "current_value": round(current_value, 3),
            "baseline_value": round(baseline_value, 3),
            "percent_change": round(pct_change, 1),
            "volatility": round(volatility, 3),
            "min_value": round(min(values), 3),
            "max_value": round(max(values), 3),
            "avg_value": round(statistics.mean(values), 3),
        }

    def _detect_change_points(
        self, points: List[TrendDataPoint], window_size: int = 7, threshold: float = 0.3
    ) -> List[ChangePoint]:
        """Detect significant change points using sliding window"""
        change_points = []

        if len(points) < window_size * 2:
            return change_points

        for i in range(window_size, len(points) - window_size):
            # Calculate means before and after window
            before_window = points[i - window_size : i]
            after_window = points[i : i + window_size]

            before_mean = statistics.mean(p.value for p in before_window)
            after_mean = statistics.mean(p.value for p in after_window)

            # Calculate change magnitude
            if before_mean > 0:
                pct_change = abs((after_mean - before_mean) / before_mean)
            else:
                pct_change = abs(after_mean - before_mean)

            # Check if threshold exceeded
            if pct_change > threshold:
                change_type = "increase" if after_mean > before_mean else "decrease"

                # Additional classification
                if pct_change > 0.5:
                    change_type = "spike" if after_mean > before_mean else "drop"

                change_points.append(
                    ChangePoint(
                        date=points[i].date,
                        change_type=change_type,
                        magnitude=round(pct_change, 3),
                        confidence=min(1.0, pct_change / threshold * 0.5),
                        context={
                            "before_mean": round(before_mean, 3),
                            "after_mean": round(after_mean, 3),
                        },
                    )
                )

        return change_points

    def _detect_seasonal_patterns(
        self, points: List[TrendDataPoint]
    ) -> List[SeasonalPattern]:
        """Detect seasonal patterns in data"""
        patterns = []

        if len(points) < 14:  # Need at least 2 weeks
            return patterns

        # Group by day of week
        dow_values = defaultdict(list)
        for point in points:
            dow = point.date.weekday()
            dow_values[dow].append(point.value)

        # Calculate weekly pattern
        if len(dow_values) == 7:  # All days present
            dow_avgs = {dow: statistics.mean(vals) for dow, vals in dow_values.items()}

            day_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            peak_days = [
                day_names[dow]
                for dow, avg in sorted(
                    dow_avgs.items(), key=lambda x: x[1], reverse=True
                )[:2]
            ]
            trough_days = [
                day_names[dow]
                for dow, avg in sorted(dow_avgs.items(), key=lambda x: x[1])[:2]
            ]

            patterns.append(
                SeasonalPattern(
                    pattern_type="weekly",
                    period="day_of_week",
                    average_value=round(statistics.mean(dow_avgs.values()), 3),
                    peak_times=peak_days,
                    trough_times=trough_days,
                )
            )

        return patterns

    async def _calculate_comparative_metrics(
        self, points: List[TrendDataPoint], total_days: int
    ) -> Dict[str, Any]:
        """Calculate period-over-period comparisons"""
        if len(points) < total_days // 2:
            return {"insufficient_data": True}

        midpoint = len(points) // 2

        first_period = points[:midpoint]
        second_period = points[midpoint:]

        first_avg = statistics.mean(p.value for p in first_period)
        second_avg = statistics.mean(p.value for p in second_period)

        period_comparison = (
            ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        )

        return {
            "first_period_avg": round(first_avg, 3),
            "second_period_avg": round(second_avg, 3),
            "period_comparison_pct": round(period_comparison, 1),
            "improvement": period_comparison < 0,  # Lower is better
        }

    def _generate_forecast(
        self, points: List[TrendDataPoint], forecast_days: int = 30
    ) -> Dict[str, Any]:
        """Generate simple forecast using linear trend"""
        if len(points) < 5:
            return {"insufficient_data": True}

        values = [p.value for p in points]

        # Simple linear projection
        x = list(range(len(values)))
        n = len(values)

        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi**2 for xi in x)

        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x**2)
        intercept = (sum_y - slope * sum_x) / n

        # Generate forecast points
        forecast = []
        last_date = points[-1].date

        for day in range(1, forecast_days + 1):
            forecast_value = slope * (len(values) + day - 1) + intercept
            forecast_date = last_date + timedelta(days=day)

            forecast.append(
                {
                    "date": forecast_date.isoformat(),
                    "forecast_value": round(max(0, min(1, forecast_value)), 3),
                    "zone": self._severity_to_zone(max(0, min(1, forecast_value))),
                }
            )

        return {
            "method": "linear_regression",
            "forecast_days": forecast_days,
            "slope": round(slope, 4),
            "intercept": round(intercept, 3),
            "forecast": forecast,
        }

    def _severity_to_float(self, severity: str) -> float:
        """Convert severity level to float"""
        severity_map = {
            ToxicityLevel.NONE: 0.0,
            ToxicityLevel.LOW: 0.2,
            ToxicityLevel.MEDIUM: 0.5,
            ToxicityLevel.HIGH: 0.7,
            ToxicityLevel.CRITICAL: 1.0,
        }
        return severity_map.get(severity, 0.5)

    def _severity_to_zone(self, severity: float) -> str:
        """Convert severity to zone"""
        if severity >= 0.6:
            return "red"
        elif severity >= 0.3:
            return "yellow"
        else:
            return "green"

    def _serialize_change_point(self, cp: ChangePoint) -> Dict[str, Any]:
        """Serialize change point for JSON"""
        return {
            "date": cp.date.isoformat(),
            "change_type": cp.change_type,
            "magnitude": cp.magnitude,
            "confidence": cp.confidence,
            "context": cp.context,
        }

    def _serialize_seasonal(self, sp: SeasonalPattern) -> Dict[str, Any]:
        """Serialize seasonal pattern for JSON"""
        return {
            "pattern_type": sp.pattern_type,
            "period": sp.period,
            "average_value": sp.average_value,
            "peak_times": sp.peak_times,
            "trough_times": sp.trough_times,
        }


# Singleton instance
longitudinal_trend_analyzer = LongitudinalTrendAnalyzer()
