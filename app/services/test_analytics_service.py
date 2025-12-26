"""
Test Analytics and Reporting Service
Provides comprehensive test analytics, dashboards, and insights
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
from pathlib import Path
import json
import uuid
from statistics import mean, median, stdev
from collections import defaultdict, Counter

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from app.core.config import settings
from app.services.qa_service import ManualQAService
from app.services.usability_service import UsabilityTestingService
from app.services.accessibility_service import AccessibilityAuditService
from app.services.beta_feedback_service import BetaFeedbackService
from app.services.automated_ui_testing_service import AutomatedUITestingService

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of test metrics"""
    COVERAGE = "coverage"
    PASS_RATE = "pass_rate"
    EXECUTION_TIME = "execution_time"
    DEFECT_DENSITY = "defect_density"
    USER_SATISFACTION = "user_satisfaction"
    ACCESSIBILITY_SCORE = "accessibility_score"
    PERFORMANCE = "performance"
    RELIABILITY = "reliability"


class TimePeriod(Enum):
    """Time periods for analytics"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"


class TestPhase(Enum):
    """Testing phases"""
    PLANNING = "planning"
    DESIGN = "design"
    EXECUTION = "execution"
    ANALYSIS = "analysis"
    REPORTING = "reporting"


class QualityGate(Enum):
    """Quality gate statuses"""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class TestMetric:
    """Individual test metric"""
    id: str
    name: str
    metric_type: MetricType
    value: float
    unit: str
    target: Optional[float] = None
    threshold: Optional[float] = None
    status: str = "neutral"  # good, warning, critical
    trend: Optional[float] = None  # Percentage change from previous period
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class TestHealthScore:
    """Overall test health score"""
    overall_score: float
    coverage_score: float
    quality_score: float
    performance_score: float
    user_experience_score: float
    accessibility_score: float
    reliability_score: float
    trends: Dict[str, float]
    recommendations: List[str]
    grade: str  # A, B, C, D, F


@dataclass
class TestTrend:
    """Test metric trend over time"""
    metric_name: str
    time_series: List[Tuple[datetime, float]]
    trend_direction: str  # improving, declining, stable
    trend_strength: float  # 0-1, how strong the trend is
    seasonality: Optional[str] = None
    forecast: Optional[List[Tuple[datetime, float]]] = None


@dataclass
class QualityGateResult:
    """Quality gate evaluation result"""
    gate_name: str
    status: QualityGate
    criteria_met: List[str]
    criteria_failed: List[str]
    score: float
    blocking: bool = False
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TestingDashboard:
    """Complete testing analytics dashboard"""
    id: str
    name: str
    description: str
    time_period: TimePeriod
    start_date: datetime
    end_date: datetime
    health_score: TestHealthScore
    key_metrics: List[TestMetric]
    trends: List[TestTrend]
    quality_gates: List[QualityGateResult]
    test_execution_summary: Dict[str, Any]
    risk_assessment: Dict[str, Any]
    recommendations: List[str]
    last_updated: datetime = field(default_factory=datetime.utcnow)


class TestAnalyticsService:
    """Comprehensive test analytics and reporting service"""

    def __init__(self):
        self.qa_service = ManualQAService()
        self.usability_service = UsabilityTestingService()
        self.accessibility_service = AccessibilityAuditService()
        self.beta_feedback_service = BetaFeedbackService()
        self.ui_testing_service = AutomatedUITestingService()

        # Metric thresholds and targets
        self.metric_targets = {
            MetricType.COVERAGE: {"target": 80.0, "threshold": 70.0},
            MetricType.PASS_RATE: {"target": 95.0, "threshold": 85.0},
            MetricType.EXECUTION_TIME: {"target": 300.0, "threshold": 600.0},  # seconds
            MetricType.USER_SATISFACTION: {"target": 4.0, "threshold": 3.0},  # 1-5 scale
            MetricType.ACCESSIBILITY_SCORE: {"target": 90.0, "threshold": 75.0},
            MetricType.PERFORMANCE: {"target": 2.0, "threshold": 4.0},  # load time seconds
        }

    async def generate_test_dashboard(
        self,
        time_period: TimePeriod = TimePeriod.WEEKLY,
        custom_start_date: Optional[datetime] = None,
        custom_end_date: Optional[datetime] = None
    ) -> TestingDashboard:
        """Generate comprehensive testing analytics dashboard"""
        logger.info(f"Generating test dashboard for period: {time_period.value}")

        # Determine date range
        end_date = custom_end_date or datetime.utcnow()
        start_date = custom_start_date or self._calculate_start_date(end_date, time_period)

        dashboard_id = str(uuid.uuid4())

        # Collect data from all testing services
        qa_metrics = await self._collect_qa_metrics(start_date, end_date)
        usability_metrics = await self._collect_usability_metrics(start_date, end_date)
        accessibility_metrics = await self._collect_accessibility_metrics(start_date, end_date)
        feedback_metrics = await self._collect_feedback_metrics(start_date, end_date)
        ui_test_metrics = await self._collect_ui_test_metrics(start_date, end_date)

        # Calculate health score
        health_score = await self._calculate_health_score(
            qa_metrics, usability_metrics, accessibility_metrics,
            feedback_metrics, ui_test_metrics
        )

        # Generate key metrics
        key_metrics = await self._generate_key_metrics(
            qa_metrics, usability_metrics, accessibility_metrics,
            feedback_metrics, ui_test_metrics
        )

        # Analyze trends
        trends = await self._analyze_trends(start_date, end_date, time_period)

        # Evaluate quality gates
        quality_gates = await self._evaluate_quality_gates(key_metrics, health_score)

        # Generate test execution summary
        execution_summary = await self._generate_execution_summary(
            qa_metrics, usability_metrics, accessibility_metrics,
            feedback_metrics, ui_test_metrics
        )

        # Assess risks
        risk_assessment = await self._assess_risks(
            key_metrics, health_score, trends, quality_gates
        )

        # Generate recommendations
        recommendations = await self._generate_recommendations(
            health_score, key_metrics, trends, quality_gates, risk_assessment
        )

        dashboard = TestingDashboard(
            id=dashboard_id,
            name=f"Test Analytics Dashboard - {time_period.value.title()}",
            description=f"Comprehensive testing analytics for {time_period.value} period",
            time_period=time_period,
            start_date=start_date,
            end_date=end_date,
            health_score=health_score,
            key_metrics=key_metrics,
            trends=trends,
            quality_gates=quality_gates,
            test_execution_summary=execution_summary,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )

        logger.info(f"Test dashboard generated: {dashboard_id}")
        return dashboard

    def _calculate_start_date(self, end_date: datetime, period: TimePeriod) -> datetime:
        """Calculate start date based on time period"""
        if period == TimePeriod.HOURLY:
            return end_date - timedelta(hours=24)
        elif period == TimePeriod.DAILY:
            return end_date - timedelta(days=7)
        elif period == TimePeriod.WEEKLY:
            return end_date - timedelta(weeks=4)
        elif period == TimePeriod.MONTHLY:
            return end_date - timedelta(days=90)
        elif period == TimePeriod.QUARTERLY:
            return end_date - timedelta(days=365)
        else:
            return end_date - timedelta(weeks=1)

    async def _collect_qa_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect manual QA metrics"""
        try:
            # Get test execution statistics
            test_plans = await self.qa_service.get_test_plans()
            active_plans = [p for p in test_plans if p.status in ["active", "in_progress"]]

            total_tests = sum(len(p.test_cases) for p in active_plans)
            executed_tests = sum(
                len([tc for tc in p.test_cases if tc.status != "not_executed"])
                for p in active_plans
            )
            passed_tests = sum(
                len([tc for tc in p.test_cases if tc.status == "passed"])
                for p in active_plans
            )

            pass_rate = (passed_tests / executed_tests * 100) if executed_tests > 0 else 0
            execution_rate = (executed_tests / total_tests * 100) if total_tests > 0 else 0

            # Calculate defect density
            failed_tests = executed_tests - passed_tests
            defect_density = (failed_tests / total_tests * 100) if total_tests > 0 else 0

            return {
                "total_test_plans": len(active_plans),
                "total_test_cases": total_tests,
                "executed_tests": executed_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "pass_rate": pass_rate,
                "execution_rate": execution_rate,
                "defect_density": defect_density,
                "coverage": execution_rate  # Using execution rate as coverage metric
            }

        except Exception as e:
            logger.error(f"Error collecting QA metrics: {str(e)}")
            return {}

    async def _collect_usability_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect usability testing metrics"""
        try:
            # Get completed usability sessions
            sessions = await self.usability_service.get_completed_sessions(
                start_date=start_date,
                end_date=end_date
            )

            if not sessions:
                return {
                    "total_sessions": 0,
                    "average_sus_score": 0,
                    "task_completion_rate": 0,
                    "average_task_time": 0,
                    "user_satisfaction": 0
                }

            # Calculate SUS scores
            sus_scores = [s.final_sus_score for s in sessions if s.final_sus_score]
            avg_sus_score = mean(sus_scores) if sus_scores else 0

            # Calculate task completion rates
            all_tasks = []
            completed_tasks = 0
            total_task_time = 0

            for session in sessions:
                for task in session.task_results:
                    all_tasks.append(task)
                    if task.completed_successfully:
                        completed_tasks += 1
                    total_task_time += task.time_to_complete or 0

            task_completion_rate = (completed_tasks / len(all_tasks) * 100) if all_tasks else 0
            avg_task_time = (total_task_time / len(all_tasks)) if all_tasks else 0

            # Convert SUS score to satisfaction metric (0-5 scale)
            user_satisfaction = (avg_sus_score / 100 * 5) if avg_sus_score > 0 else 0

            return {
                "total_sessions": len(sessions),
                "average_sus_score": avg_sus_score,
                "task_completion_rate": task_completion_rate,
                "average_task_time": avg_task_time,
                "user_satisfaction": user_satisfaction
            }

        except Exception as e:
            logger.error(f"Error collecting usability metrics: {str(e)}")
            return {}

    async def _collect_accessibility_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect accessibility testing metrics"""
        try:
            # Run accessibility audit on main application pages
            audit_urls = [
                "http://localhost:3000",
                "http://localhost:3000/login",
                "http://localhost:3000/dashboard",
                "http://localhost:3000/assessments"
            ]

            total_audits = 0
            total_issues = 0
            total_score = 0

            for url in audit_urls:
                try:
                    audit = await self.accessibility_service.run_accessibility_audit(url)
                    total_audits += 1
                    total_issues += len(audit.issues)
                    total_score += audit.score

                except Exception as e:
                    logger.warning(f"Failed to audit {url}: {str(e)}")
                    continue

            avg_score = (total_score / total_audits) if total_audits > 0 else 0
            avg_issues = (total_issues / total_audits) if total_audits > 0 else 0

            return {
                "total_audits": total_audits,
                "average_score": avg_score,
                "average_issues": avg_issues,
                "compliance_percentage": avg_score  # Using score as compliance percentage
            }

        except Exception as e:
            logger.error(f"Error collecting accessibility metrics: {str(e)}")
            return {}

    async def _collect_feedback_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect beta feedback metrics"""
        try:
            # Get feedback summary
            summary = await self.beta_feedback_service.get_feedback_summary(
                days=(end_date - start_date).days
            )

            # Analyze feedback sentiment
            total_submissions = summary["total_submissions"]
            avg_satisfaction = summary["average_satisfaction"]

            # Categorize feedback
            bug_reports = summary["by_type"].get("bug_report", 0)
            feature_requests = summary["by_type"].get("feature_request", 0)
            usability_issues = summary["by_type"].get("usability_issue", 0)

            return {
                "total_submissions": total_submissions,
                "average_satisfaction": avg_satisfaction,
                "bug_reports": bug_reports,
                "feature_requests": feature_requests,
                "usability_issues": usability_issues,
                "user_satisfaction": avg_satisfaction
            }

        except Exception as e:
            logger.error(f"Error collecting feedback metrics: {str(e)}")
            return {}

    async def _collect_ui_test_metrics(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Collect automated UI testing metrics"""
        try:
            # Get test execution history
            executions = await self.ui_testing_service.get_test_execution_history(
                days=(end_date - start_date).days
            )

            if not executions:
                return {
                    "total_executions": 0,
                    "pass_rate": 0,
                    "average_duration": 0,
                    "failed_tests": 0
                }

            total_executions = len(executions)
            passed_tests = len([e for e in executions if e.status.value == "passed"])
            failed_tests = len([e for e in executions if e.status.value == "failed"])

            pass_rate = (passed_tests / total_executions * 100) if total_executions > 0 else 0
            avg_duration = mean([e.duration or 0 for e in executions])

            return {
                "total_executions": total_executions,
                "pass_rate": pass_rate,
                "average_duration": avg_duration,
                "failed_tests": failed_tests
            }

        except Exception as e:
            logger.error(f"Error collecting UI test metrics: {str(e)}")
            return {}

    async def _calculate_health_score(
        self,
        qa_metrics: Dict[str, Any],
        usability_metrics: Dict[str, Any],
        accessibility_metrics: Dict[str, Any],
        feedback_metrics: Dict[str, Any],
        ui_test_metrics: Dict[str, Any]
    ) -> TestHealthScore:
        """Calculate overall test health score"""
        # Coverage score (0-100)
        coverage_score = qa_metrics.get("coverage", 0)

        # Quality score (0-100) - combination of pass rates
        qa_pass_rate = qa_metrics.get("pass_rate", 0)
        ui_pass_rate = ui_test_metrics.get("pass_rate", 0)
        quality_score = (qa_pass_rate + ui_pass_rate) / 2

        # Performance score (0-100) - inverted execution time
        avg_duration = ui_test_metrics.get("average_duration", 300)
        performance_score = max(0, 100 - (avg_duration / 10))  # 10 points per 10 seconds

        # User experience score (0-100)
        usability_satisfaction = usability_metrics.get("user_satisfaction", 0) * 20  # Convert to 0-100
        feedback_satisfaction = feedback_metrics.get("user_satisfaction", 0) * 20  # Convert to 0-100
        user_experience_score = (usability_satisfaction + feedback_satisfaction) / 2

        # Accessibility score (0-100)
        accessibility_score = accessibility_metrics.get("compliance_percentage", 0)

        # Reliability score (0-100) - based on low defect density
        defect_density = qa_metrics.get("defect_density", 100)
        reliability_score = max(0, 100 - defect_density)

        # Overall score (weighted average)
        overall_score = (
            coverage_score * 0.2 +
            quality_score * 0.25 +
            performance_score * 0.15 +
            user_experience_score * 0.2 +
            accessibility_score * 0.1 +
            reliability_score * 0.1
        )

        # Determine grade
        if overall_score >= 90:
            grade = "A"
        elif overall_score >= 80:
            grade = "B"
        elif overall_score >= 70:
            grade = "C"
        elif overall_score >= 60:
            grade = "D"
        else:
            grade = "F"

        return TestHealthScore(
            overall_score=overall_score,
            coverage_score=coverage_score,
            quality_score=quality_score,
            performance_score=performance_score,
            user_experience_score=user_experience_score,
            accessibility_score=accessibility_score,
            reliability_score=reliability_score,
            trends={},  # Would calculate historical trends
            recommendations=[],  # Will be populated later
            grade=grade
        )

    async def _generate_key_metrics(
        self,
        qa_metrics: Dict[str, Any],
        usability_metrics: Dict[str, Any],
        accessibility_metrics: Dict[str, Any],
        feedback_metrics: Dict[str, Any],
        ui_test_metrics: Dict[str, Any]
    ) -> List[TestMetric]:
        """Generate key performance metrics"""
        metrics = []

        # Test Coverage
        coverage = qa_metrics.get("coverage", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="Test Coverage",
            metric_type=MetricType.COVERAGE,
            value=coverage,
            unit="%",
            target=self.metric_targets[MetricType.COVERAGE]["target"],
            threshold=self.metric_targets[MetricType.COVERAGE]["threshold"],
            status=self._get_metric_status(coverage, MetricType.COVERAGE)
        ))

        # Pass Rate
        pass_rate = qa_metrics.get("pass_rate", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="Test Pass Rate",
            metric_type=MetricType.PASS_RATE,
            value=pass_rate,
            unit="%",
            target=self.metric_targets[MetricType.PASS_RATE]["target"],
            threshold=self.metric_targets[MetricType.PASS_RATE]["threshold"],
            status=self._get_metric_status(pass_rate, MetricType.PASS_RATE)
        ))

        # User Satisfaction
        satisfaction = usability_metrics.get("user_satisfaction", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="User Satisfaction",
            metric_type=MetricType.USER_SATISFACTION,
            value=satisfaction,
            unit="score",
            target=self.metric_targets[MetricType.USER_SATISFACTION]["target"],
            threshold=self.metric_targets[MetricType.USER_SATISFACTION]["threshold"],
            status=self._get_metric_status(satisfaction, MetricType.USER_SATISFACTION)
        ))

        # Accessibility Score
        accessibility_score = accessibility_metrics.get("compliance_percentage", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="Accessibility Score",
            metric_type=MetricType.ACCESSIBILITY_SCORE,
            value=accessibility_score,
            unit="%",
            target=self.metric_targets[MetricType.ACCESSIBILITY_SCORE]["target"],
            threshold=self.metric_targets[MetricType.ACCESSIBILITY_SCORE]["threshold"],
            status=self._get_metric_status(accessibility_score, MetricType.ACCESSIBILITY_SCORE)
        ))

        # Average Execution Time
        exec_time = ui_test_metrics.get("average_duration", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="Average Test Execution Time",
            metric_type=MetricType.EXECUTION_TIME,
            value=exec_time,
            unit="seconds",
            target=self.metric_targets[MetricType.EXECUTION_TIME]["target"],
            threshold=self.metric_targets[MetricType.EXECUTION_TIME]["threshold"],
            status=self._get_metric_status(exec_time, MetricType.EXECUTION_TIME, invert=True)
        ))

        # Defect Density
        defect_density = qa_metrics.get("defect_density", 0)
        metrics.append(TestMetric(
            id=str(uuid.uuid4()),
            name="Defect Density",
            metric_type=MetricType.DEFECT_DENSITY,
            value=defect_density,
            unit="%",
            target=5.0,  # Target less than 5% defects
            threshold=10.0,  # Threshold less than 10% defects
            status=self._get_metric_status(100 - defect_density, MetricType.PASS_RATE, invert=True)
        ))

        return metrics

    def _get_metric_status(self, value: float, metric_type: MetricType, invert: bool = False) -> str:
        """Determine metric status based on value and thresholds"""
        target = self.metric_targets.get(metric_type, {}).get("target", 0)
        threshold = self.metric_targets.get(metric_type, {}).get("threshold", 0)

        if invert:
            # For metrics where lower is better (like execution time)
            if value <= target:
                return "good"
            elif value <= threshold:
                return "warning"
            else:
                return "critical"
        else:
            # For metrics where higher is better
            if value >= target:
                return "good"
            elif value >= threshold:
                return "warning"
            else:
                return "critical"

    async def _analyze_trends(
        self,
        start_date: datetime,
        end_date: datetime,
        period: TimePeriod
    ) -> List[TestTrend]:
        """Analyze trends in test metrics over time"""
        trends = []

        # This would typically involve querying historical data
        # For now, returning placeholder trends

        trends.append(TestTrend(
            metric_name="Test Coverage",
            time_series=[],  # Would contain historical data points
            trend_direction="stable",
            trend_strength=0.8,
            forecast=[]  # Would contain forecasted values
        ))

        trends.append(TestTrend(
            metric_name="Pass Rate",
            time_series=[],
            trend_direction="improving",
            trend_strength=0.6,
            forecast=[]
        ))

        return trends

    async def _evaluate_quality_gates(
        self,
        key_metrics: List[TestMetric],
        health_score: TestHealthScore
    ) -> List[QualityGateResult]:
        """Evaluate quality gates against metrics"""
        gates = []

        # Coverage Quality Gate
        coverage_metric = next((m for m in key_metrics if m.metric_type == MetricType.COVERAGE), None)
        if coverage_metric:
            coverage_passed = coverage_metric.value >= coverage_metric.target
            gates.append(QualityGateResult(
                gate_name="Code Coverage",
                status=QualityGate.PASSED if coverage_passed else QualityGate.FAILED,
                criteria_met=["Coverage >= 80%"] if coverage_passed else [],
                criteria_failed=["Coverage < 80%"] if not coverage_passed else [],
                score=coverage_metric.value,
                blocking=not coverage_passed
            ))

        # Quality Gate
        pass_rate_metric = next((m for m in key_metrics if m.metric_type == MetricType.PASS_RATE), None)
        if pass_rate_metric:
            quality_passed = pass_rate_metric.value >= pass_rate_metric.target
            gates.append(QualityGateResult(
                gate_name="Test Quality",
                status=QualityGate.PASSED if quality_passed else QualityGate.WARNING,
                criteria_met=["Pass Rate >= 95%"] if quality_passed else [],
                criteria_failed=["Pass Rate < 95%"] if not quality_passed else [],
                score=pass_rate_metric.value,
                blocking=False
            ))

        # User Experience Quality Gate
        satisfaction_metric = next((m for m in key_metrics if m.metric_type == MetricType.USER_SATISFACTION), None)
        if satisfaction_metric:
            ux_passed = satisfaction_metric.value >= satisfaction_metric.target
            gates.append(QualityGateResult(
                gate_name="User Experience",
                status=QualityGate.PASSED if ux_passed else QualityGate.WARNING,
                criteria_met=["Satisfaction >= 4.0"] if ux_passed else [],
                criteria_failed=["Satisfaction < 4.0"] if not ux_passed else [],
                score=satisfaction_metric.value,
                blocking=False
            ))

        # Overall Quality Gate
        gates.append(QualityGateResult(
            gate_name="Overall Quality",
            status=QualityGate.PASSED if health_score.overall_score >= 80 else QualityGate.WARNING,
            criteria_met=["Overall Score >= 80"] if health_score.overall_score >= 80 else [],
            criteria_failed=["Overall Score < 80"] if health_score.overall_score < 80 else [],
            score=health_score.overall_score,
            blocking=False,
            details={
                "grade": health_score.grade,
                "breakdown": {
                    "coverage": health_score.coverage_score,
                    "quality": health_score.quality_score,
                    "performance": health_score.performance_score,
                    "user_experience": health_score.user_experience_score,
                    "accessibility": health_score.accessibility_score,
                    "reliability": health_score.reliability_score
                }
            }
        ))

        return gates

    async def _generate_execution_summary(
        self,
        qa_metrics: Dict[str, Any],
        usability_metrics: Dict[str, Any],
        accessibility_metrics: Dict[str, Any],
        feedback_metrics: Dict[str, Any],
        ui_test_metrics: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive test execution summary"""
        return {
            "manual_testing": {
                "test_plans": qa_metrics.get("total_test_plans", 0),
                "test_cases": qa_metrics.get("total_test_cases", 0),
                "executed": qa_metrics.get("executed_tests", 0),
                "pass_rate": qa_metrics.get("pass_rate", 0),
                "coverage": qa_metrics.get("coverage", 0)
            },
            "automated_testing": {
                "executions": ui_test_metrics.get("total_executions", 0),
                "pass_rate": ui_test_metrics.get("pass_rate", 0),
                "average_duration": ui_test_metrics.get("average_duration", 0),
                "failed_tests": ui_test_metrics.get("failed_tests", 0)
            },
            "usability_testing": {
                "sessions": usability_metrics.get("total_sessions", 0),
                "average_sus_score": usability_metrics.get("average_sus_score", 0),
                "task_completion_rate": usability_metrics.get("task_completion_rate", 0),
                "user_satisfaction": usability_metrics.get("user_satisfaction", 0)
            },
            "accessibility_testing": {
                "audits": accessibility_metrics.get("total_audits", 0),
                "average_score": accessibility_metrics.get("average_score", 0),
                "issues_found": accessibility_metrics.get("average_issues", 0),
                "compliance_rate": accessibility_metrics.get("compliance_percentage", 0)
            },
            "user_feedback": {
                "total_submissions": feedback_metrics.get("total_submissions", 0),
                "average_satisfaction": feedback_metrics.get("user_satisfaction", 0),
                "bug_reports": feedback_metrics.get("bug_reports", 0),
                "feature_requests": feedback_metrics.get("feature_requests", 0)
            }
        }

    async def _assess_risks(
        self,
        key_metrics: List[TestMetric],
        health_score: TestHealthScore,
        trends: List[TestTrend],
        quality_gates: List[QualityGateResult]
    ) -> Dict[str, Any]:
        """Assess testing risks and issues"""
        risks = {
            "high_risk": [],
            "medium_risk": [],
            "low_risk": [],
            "opportunities": []
        }

        # Check for critical metric issues
        for metric in key_metrics:
            if metric.status == "critical":
                risks["high_risk"].append(f"{metric.name} is critical: {metric.value}{metric.unit}")
            elif metric.status == "warning":
                risks["medium_risk"].append(f"{metric.name} needs attention: {metric.value}{metric.unit}")

        # Check quality gate failures
        for gate in quality_gates:
            if gate.status == QualityGate.FAILED and gate.blocking:
                risks["high_risk"].append(f"Blocking quality gate failed: {gate.gate_name}")
            elif gate.status == QualityGate.FAILED:
                risks["medium_risk"].append(f"Quality gate failed: {gate.gate_name}")

        # Check overall health
        if health_score.grade in ["D", "F"]:
            risks["high_risk"].append(f"Overall test health is poor: Grade {health_score.grade}")
        elif health_score.grade == "C":
            risks["medium_risk"].append(f"Overall test health needs improvement: Grade {health_score.grade}")

        # Identify opportunities
        for metric in key_metrics:
            if metric.status == "good" and metric.value > metric.target * 1.1:
                risks["opportunities"].append(f"{metric.name} exceeds targets: {metric.value}{metric.unit}")

        return risks

    async def _generate_recommendations(
        self,
        health_score: TestHealthScore,
        key_metrics: List[TestMetric],
        trends: List[TestTrend],
        quality_gates: List[QualityGateResult],
        risk_assessment: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []

        # Health-based recommendations
        if health_score.overall_score < 70:
            recommendations.append(
                "URGENT: Overall test health is below acceptable levels. "
                "Focus on improving test coverage and quality metrics."
            )

        # Metric-specific recommendations
        for metric in key_metrics:
            if metric.status == "critical":
                if metric.metric_type == MetricType.COVERAGE:
                    recommendations.append(
                        f"Increase test coverage from {metric.value:.1f}% to target {metric.target}%. "
                        "Focus on uncovered critical paths and edge cases."
                    )
                elif metric.metric_type == MetricType.PASS_RATE:
                    recommendations.append(
                        f"Improve test pass rate from {metric.value:.1f}% to target {metric.target}%. "
                        "Review and fix failing tests, check test environment stability."
                    )
                elif metric.metric_type == MetricType.USER_SATISFACTION:
                    recommendations.append(
                        f"Address user satisfaction issues (current: {metric.value:.1f}). "
                        "Review usability feedback and prioritize user experience improvements."
                    )

        # Quality gate recommendations
        for gate in quality_gates:
            if gate.status == QualityGate.FAILED:
                recommendations.append(f"Address quality gate failures for {gate.gate_name}")

        # Risk-based recommendations
        for risk in risk_assessment["high_risk"]:
            recommendations.append(f"HIGH PRIORITY: {risk}")

        # Opportunities
        if risk_assessment["opportunities"]:
            recommendations.append(
                "Consider leveraging strengths identified in testing performance "
                "to optimize other areas of quality assurance."
            )

        return recommendations

    async def export_dashboard_data(
        self,
        dashboard_id: str,
        format: str = "json"
    ) -> str:
        """Export dashboard data in specified format"""
        # This would retrieve dashboard and export in requested format
        # For now, returning placeholder
        return f"Dashboard {dashboard_id} exported as {format}"

    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time testing metrics"""
        return {
            "currently_running_tests": 0,  # Would check active test executions
            "recent_failures": 0,  # Would count recent test failures
            "system_health": "healthy",  # Would check system status
            "last_update": datetime.utcnow().isoformat()
        }


# Initialize the test analytics service
test_analytics_service = TestAnalyticsService()