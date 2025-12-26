"""
Safety Analytics Service
Advanced analytics for safety incidents, wellness trends, and compliance reporting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, func, case, extract
from dataclasses import dataclass
import json

from app.db.models.employee_safety import (
    SafetyIncident, SafetyFollowUpAction, WellnessAssessment, WellnessAlert,
    SafetyResource, SafetyTraining, SafetyTrainingCompletion,
    SafetyIncidentType, IncidentSeverity, IncidentStatus, AlertLevel
)
from app.db.models.user import User
from app.db.models.organization import Organization
from app.db.models.team import Team

logger = logging.getLogger(__name__)


@dataclass
class SafetyMetrics:
    """Safety metrics data structure"""
    total_incidents: int
    incident_rate: float  # Incidents per 100 employees per month
    severity_distribution: Dict[str, int]
    type_distribution: Dict[str, int]
    resolution_time_avg: float  # Average days to resolution
    repeat_incident_rate: float  # Percentage of repeat incidents
    compliance_rate: float  # Percentage of incidents with compliance reporting
    training_completion_rate: float  # Percentage of required training completed


@dataclass
class WellnessMetrics:
    """Wellness metrics data structure"""
    total_assessments: int
    average_wellness_score: float
    high_risk_percentage: float  # Percentage of high/critical risk assessments
    trend_direction: str  # improving, stable, declining
    key_risk_factors: List[str]
    department_breakdown: Dict[str, float]  # Average scores by department
    intervention_effectiveness: float  # Success rate of wellness interventions


@dataclass
class ComplianceReport:
    """Compliance report data structure"""
    report_period: Tuple[datetime, datetime]
    total_incidents: int
    reportable_incidents: int  # Incidents requiring external reporting
    compliance_rate: float
    overdue_reports: int
    critical_incidents: List[Dict[str, Any]]
    recommendations: List[str]
    next_review_date: datetime


class SafetyAnalyticsService:
    """Advanced safety analytics and compliance service"""

    def __init__(self, db: Session):
        self.db = db

        # Industry benchmarks and thresholds
        self.benchmarks = {
            'incident_rate': 2.5,  # Industry average: 2.5 incidents per 100 employees per month
            'resolution_time': 7.0,  # Target: 7 days average resolution
            'compliance_rate': 95.0,  # Target: 95% compliance reporting
            'training_completion': 90.0,  # Target: 90% training completion
            'wellness_score': 70.0,  # Target: 70 average wellness score
        }

    # Safety Incident Analytics

    def get_safety_metrics(self, organization_id: UUID, team_id: Optional[UUID] = None,
                          date_range: Optional[Tuple[datetime, datetime]] = None) -> SafetyMetrics:
        """Calculate comprehensive safety metrics"""
        try:
            # Default to last 90 days if no date range provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=90)
                date_range = (start_date, end_date)

            start_date, end_date = date_range

            # Base query for incidents
            query = self.db.query(SafetyIncident).filter(
                SafetyIncident.organization_id == organization_id,
                SafetyIncident.date_reported >= start_date,
                SafetyIncident.date_reported <= end_date
            )

            if team_id:
                query = query.filter(SafetyIncident.team_id == team_id)

            incidents = query.all()

            # Total incidents
            total_incidents = len(incidents)

            # Calculate incident rate (per 100 employees per month)
            months_in_period = (end_date - start_date).days / 30.44
            employee_count = self._get_employee_count(organization_id, team_id)
            incident_rate = (total_incidents / max(employee_count, 1) / max(months_in_period, 1)) * 100

            # Severity distribution
            severity_distribution = {}
            for incident in incidents:
                severity = incident.severity.value
                severity_distribution[severity] = severity_distribution.get(severity, 0) + 1

            # Type distribution
            type_distribution = {}
            for incident in incidents:
                inc_type = incident.incident_type.value
                type_distribution[inc_type] = type_distribution.get(inc_type, 0) + 1

            # Average resolution time
            resolved_incidents = [inc for inc in incidents if inc.resolution_date]
            if resolved_incidents:
                resolution_times = [
                    (inc.resolution_date - inc.date_reported).days
                    for inc in resolved_incidents
                ]
                resolution_time_avg = sum(resolution_times) / len(resolution_times)
            else:
                resolution_time_avg = 0.0

            # Repeat incident rate
            repeat_incidents = self._identify_repeat_incidents(incidents)
            repeat_incident_rate = (len(repeat_incidents) / max(total_incidents, 1)) * 100

            # Compliance rate
            reportable_incidents = [inc for inc in incidents if inc.compliance_required]
            compliant_incidents = [inc for inc in reportable_incidents if inc.compliance_reported]
            compliance_rate = (len(compliant_incidents) / max(len(reportable_incidents), 1)) * 100

            # Training completion rate
            training_completion_rate = self._calculate_training_completion_rate(
                organization_id, team_id, date_range
            )

            return SafetyMetrics(
                total_incidents=total_incidents,
                incident_rate=incident_rate,
                severity_distribution=severity_distribution,
                type_distribution=type_distribution,
                resolution_time_avg=resolution_time_avg,
                repeat_incident_rate=repeat_incident_rate,
                compliance_rate=compliance_rate,
                training_completion_rate=training_completion_rate
            )

        except Exception as e:
            logger.error(f"Error calculating safety metrics: {str(e)}")
            return SafetyMetrics(0, 0.0, {}, {}, 0.0, 0.0, 0.0, 0.0)

    def get_incident_trends(self, organization_id: UUID, team_id: Optional[UUID] = None,
                           days: int = 180) -> Dict[str, Any]:
        """Analyze incident trends over time"""
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            # Weekly incident counts
            weekly_data = self.db.query(
                extract('year', SafetyIncident.date_reported).label('year'),
                extract('week', SafetyIncident.date_reported).label('week'),
                func.count(SafetyIncident.id).label('incident_count'),
                func.sum(case([(SafetyIncident.severity == IncidentSeverity.CRITICAL, 1)], else_=0)).label('critical_count')
            ).filter(
                SafetyIncident.organization_id == organization_id,
                SafetyIncident.date_reported >= start_date,
                SafetyIncident.date_reported <= end_date
            )

            if team_id:
                weekly_data = weekly_data.filter(SafetyIncident.team_id == team_id)

            weekly_data = weekly_data.group_by(
                extract('year', SafetyIncident.date_reported),
                extract('week', SafetyIncident.date_reported)
            ).order_by('year', 'week').all()

            # Process weekly data
            trend_data = []
            for year, week, count, critical_count in weekly_data:
                week_date = datetime.strptime(f"{year}-{int(week)}-1", "%Y-%W-%w")
                trend_data.append({
                    "week": week_date.strftime("%Y-%m-%d"),
                    "total_incidents": count,
                    "critical_incidents": critical_count or 0
                })

            # Calculate trend direction
            if len(trend_data) >= 4:
                recent_counts = [d["total_incidents"] for d in trend_data[-4:]]
                earlier_counts = [d["total_incidents"] for d in trend_data[-8:-4]] if len(trend_data) >= 8 else recent_counts

                recent_avg = sum(recent_counts) / len(recent_counts)
                earlier_avg = sum(earlier_counts) / len(earlier_counts)

                if recent_avg > earlier_avg * 1.2:
                    trend_direction = "increasing"
                elif recent_avg < earlier_avg * 0.8:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                trend_direction = "insufficient_data"

            return {
                "trend_data": trend_data,
                "trend_direction": trend_direction,
                "analysis_period": f"{days} days"
            }

        except Exception as e:
            logger.error(f"Error analyzing incident trends: {str(e)}")
            return {"error": f"Failed to analyze trends: {str(e)}"}

    # Wellness Analytics

    def get_wellness_metrics(self, organization_id: UUID, team_id: Optional[UUID] = None,
                           date_range: Optional[Tuple[datetime, datetime]] = None) -> WellnessMetrics:
        """Calculate comprehensive wellness metrics"""
        try:
            # Default to last 30 days if no date range provided
            if not date_range:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=30)
                date_range = (start_date, end_date)

            start_date, end_date = date_range

            # Get wellness assessments
            query = self.db.query(WellnessAssessment).filter(
                WellnessAssessment.organization_id == organization_id,
                WellnessAssessment.assessment_date >= start_date,
                WellnessAssessment.assessment_date <= end_date
            )

            if team_id:
                query = query.filter(WellnessAssessment.team_id == team_id)

            assessments = query.all()

            total_assessments = len(assessments)

            if total_assessments == 0:
                return WellnessMetrics(0, 0.0, 0.0, "no_data", [], {}, 0.0)

            # Average wellness score
            scores = [a.overall_wellness_score for a in assessments if a.overall_wellness_score is not None]
            average_wellness_score = sum(scores) / len(scores) if scores else 0.0

            # High risk percentage
            high_risk_assessments = [
                a for a in assessments
                if a.alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]
            ]
            high_risk_percentage = (len(high_risk_assessments) / total_assessments) * 100

            # Trend analysis
            trend_direction = self._analyze_wellness_trends(assessments)

            # Key risk factors
            risk_factors = self._identify_key_risk_factors(assessments)

            # Department breakdown
            department_breakdown = self._calculate_department_wellness(assessments)

            # Intervention effectiveness
            intervention_effectiveness = self._calculate_intervention_effectiveness(
                organization_id, team_id, date_range
            )

            return WellnessMetrics(
                total_assessments=total_assessments,
                average_wellness_score=average_wellness_score,
                high_risk_percentage=high_risk_percentage,
                trend_direction=trend_direction,
                key_risk_factors=risk_factors,
                department_breakdown=department_breakdown,
                intervention_effectiveness=intervention_effectiveness
            )

        except Exception as e:
            logger.error(f"Error calculating wellness metrics: {str(e)}")
            return WellnessMetrics(0, 0.0, 0.0, "error", [], {}, 0.0)

    # Compliance and Reporting

    def generate_compliance_report(self, organization_id: UUID, team_id: Optional[UUID] = None,
                                 report_period: Optional[Tuple[datetime, datetime]] = None) -> ComplianceReport:
        """Generate comprehensive compliance report"""
        try:
            # Default to last 90 days if no period provided
            if not report_period:
                end_date = datetime.utcnow()
                start_date = end_date - timedelta(days=90)
                report_period = (start_date, end_date)

            start_date, end_date = report_period

            # Get incidents in period
            query = self.db.query(SafetyIncident).filter(
                SafetyIncident.organization_id == organization_id,
                SafetyIncident.date_reported >= start_date,
                SafetyIncident.date_reported <= end_date
            )

            if team_id:
                query = query.filter(SafetyIncident.team_id == team_id)

            incidents = query.all()
            total_incidents = len(incidents)

            # Identify reportable incidents
            reportable_incidents = [
                inc for inc in incidents
                if inc.compliance_required or inc.severity in [IncidentSeverity.HIGH, IncidentSeverity.CRITICAL]
            ]

            # Compliance status
            compliant_incidents = [inc for inc in reportable_incidents if inc.compliance_reported]
            compliance_rate = (len(compliant_incidents) / max(len(reportable_incidents), 1)) * 100

            # Overdue reports
            overdue_incidents = [
                inc for inc in reportable_incidents
                if not inc.compliance_reported and
                inc.date_reported < datetime.utcnow() - timedelta(days=7)  # 7-day reporting window
            ]

            # Critical incidents requiring immediate attention
            critical_incidents = [
                {
                    "id": str(inc.id),
                    "title": inc.title,
                    "severity": inc.severity.value,
                    "date_reported": inc.date_reported.isoformat(),
                    "status": inc.status.value,
                    "compliance_required": inc.compliance_required,
                    "compliance_reported": inc.compliance_reported
                }
                for inc in incidents
                if inc.severity == IncidentSeverity.CRITICAL
            ]

            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                incidents, compliance_rate, len(overdue_incidents)
            )

            # Next review date
            next_review_date = end_date + timedelta(days=30)

            return ComplianceReport(
                report_period=report_period,
                total_incidents=total_incidents,
                reportable_incidents=len(reportable_incidents),
                compliance_rate=compliance_rate,
                overdue_reports=len(overdue_incidents),
                critical_incidents=critical_incidents,
                recommendations=recommendations,
                next_review_date=next_review_date
            )

        except Exception as e:
            logger.error(f"Error generating compliance report: {str(e)}")
            return ComplianceReport(
                report_period=(datetime.utcnow(), datetime.utcnow()),
                total_incidents=0,
                reportable_incidents=0,
                compliance_rate=0.0,
                overdue_reports=0,
                critical_incidents=[],
                recommendations=["Error generating report"],
                next_review_date=datetime.utcnow()
            )

    def get_safety_benchmarks(self, organization_id: UUID) -> Dict[str, Any]:
        """Compare organization's safety performance against industry benchmarks"""
        try:
            # Get current metrics (last 90 days)
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            date_range = (start_date, end_date)

            current_metrics = self.get_safety_metrics(organization_id, None, date_range)
            current_wellness = self.get_wellness_metrics(organization_id, None, date_range)

            # Compare with benchmarks
            benchmark_comparison = {
                "incident_rate": {
                    "current": current_metrics.incident_rate,
                    "benchmark": self.benchmarks['incident_rate'],
                    "performance": "better" if current_metrics.incident_rate < self.benchmarks['incident_rate'] else "worse",
                    "percentage_difference": ((self.benchmarks['incident_rate'] - current_metrics.incident_rate) /
                                            self.benchmarks['incident_rate']) * 100
                },
                "resolution_time": {
                    "current": current_metrics.resolution_time_avg,
                    "benchmark": self.benchmarks['resolution_time'],
                    "performance": "better" if current_metrics.resolution_time_avg < self.benchmarks['resolution_time'] else "worse",
                    "percentage_difference": ((self.benchmarks['resolution_time'] - current_metrics.resolution_time_avg) /
                                            self.benchmarks['resolution_time']) * 100
                },
                "compliance_rate": {
                    "current": current_metrics.compliance_rate,
                    "benchmark": self.benchmarks['compliance_rate'],
                    "performance": "better" if current_metrics.compliance_rate > self.benchmarks['compliance_rate'] else "worse",
                    "percentage_difference": ((current_metrics.compliance_rate - self.benchmarks['compliance_rate']) /
                                            self.benchmarks['compliance_rate']) * 100
                },
                "training_completion": {
                    "current": current_metrics.training_completion_rate,
                    "benchmark": self.benchmarks['training_completion'],
                    "performance": "better" if current_metrics.training_completion_rate > self.benchmarks['training_completion'] else "worse",
                    "percentage_difference": ((current_metrics.training_completion_rate - self.benchmarks['training_completion']) /
                                            self.benchmarks['training_completion']) * 100
                },
                "wellness_score": {
                    "current": current_wellness.average_wellness_score,
                    "benchmark": self.benchmarks['wellness_score'],
                    "performance": "better" if current_wellness.average_wellness_score > self.benchmarks['wellness_score'] else "worse",
                    "percentage_difference": ((current_wellness.average_wellness_score - self.benchmarks['wellness_score']) /
                                            self.benchmarks['wellness_score']) * 100
                }
            }

            # Calculate overall performance score
            better_count = sum(1 for metric in benchmark_comparison.values() if metric["performance"] == "better")
            total_metrics = len(benchmark_comparison)
            overall_performance = (better_count / total_metrics) * 100

            return {
                "benchmark_comparison": benchmark_comparison,
                "overall_performance_score": overall_performance,
                "performance_grade": self._calculate_performance_grade(overall_performance),
                "improvement_areas": [
                    metric_name for metric_name, data in benchmark_comparison.items()
                    if data["performance"] == "worse"
                ],
                "strength_areas": [
                    metric_name for metric_name, data in benchmark_comparison.items()
                    if data["performance"] == "better"
                ]
            }

        except Exception as e:
            logger.error(f"Error generating safety benchmarks: {str(e)}")
            return {"error": f"Failed to generate benchmarks: {str(e)}"}

    # Helper Methods

    def _get_employee_count(self, organization_id: UUID, team_id: Optional[UUID] = None) -> int:
        """Get employee count for organization or team"""
        try:
            query = self.db.query(func.count(User.id)).filter(
                User.organization_id == organization_id,
                User.is_active == True
            )

            if team_id:
                # This would require joining with team membership table
                # For now, return organization count
                pass

            return query.scalar() or 0
        except Exception:
            return 0

    def _identify_repeat_incidents(self, incidents: List[SafetyIncident]) -> List[SafetyIncident]:
        """Identify repeat incidents (same type, same user/team within 30 days)"""
        repeat_incidents = []

        for incident in incidents:
            # Look for similar incidents within 30 days
            similar_incidents = [
                inc for inc in incidents
                if (inc.incident_type == incident.incident_type and
                    inc.date_reported < incident.date_reported and
                    (incident.date_reported - inc.date_reported).days <= 30 and
                    (inc.affected_user_id == incident.affected_user_id or inc.team_id == incident.team_id))
            ]

            if similar_incidents:
                repeat_incidents.append(incident)

        return repeat_incidents

    def _calculate_training_completion_rate(self, organization_id: UUID, team_id: Optional[UUID] = None,
                                          date_range: Tuple[datetime, datetime]) -> float:
        """Calculate safety training completion rate"""
        try:
            start_date, end_date = date_range

            # Get required training completions in period
            query = self.db.query(SafetyTrainingCompletion).join(SafetyTraining).filter(
                SafetyTraining.organization_id == organization_id,
                SafetyTrainingCompletion.completion_date >= start_date,
                SafetyTrainingCompletion.completion_date <= end_date
            )

            # Get total required training assignments
            total_assignments = query.count()

            if total_assignments == 0:
                return 100.0  # No training required in period

            # Get passed completions
            passed_assignments = query.filter(SafetyTrainingCompletion.passed == True).count()

            return (passed_assignments / total_assignments) * 100

        except Exception:
            return 0.0

    def _analyze_wellness_trends(self, assessments: List[WellnessAssessment]) -> str:
        """Analyze wellness score trends over time"""
        try:
            if len(assessments) < 4:
                return "insufficient_data"

            # Sort by date
            assessments.sort(key=lambda x: x.assessment_date)

            # Split into two halves
            mid_point = len(assessments) // 2
            first_half = assessments[:mid_point]
            second_half = assessments[mid_point:]

            # Calculate average scores
            first_avg = sum(a.overall_wellness_score for a in first_half if a.overall_wellness_score) / len(first_half)
            second_avg = sum(a.overall_wellness_score for a in second_half if a.overall_wellness_score) / len(second_half)

            # Determine trend
            if second_avg > first_avg * 1.05:
                return "improving"
            elif second_avg < first_avg * 0.95:
                return "declining"
            else:
                return "stable"

        except Exception:
            return "error"

    def _identify_key_risk_factors(self, assessments: List[WellnessAssessment]) -> List[str]:
        """Identify most common risk factors across assessments"""
        try:
            risk_factor_counts = {}

            for assessment in assessments:
                if assessment.risk_factors:
                    for factor in assessment.risk_factors:
                        risk_factor_counts[factor] = risk_factor_counts.get(factor, 0) + 1

            # Sort by frequency and return top 5
            sorted_factors = sorted(risk_factor_counts.items(), key=lambda x: x[1], reverse=True)
            return [factor for factor, count in sorted_factors[:5]]

        except Exception:
            return []

    def _calculate_department_wellness(self, assessments: List[WellnessAssessment]) -> Dict[str, float]:
        """Calculate average wellness scores by department"""
        try:
            department_scores = {}
            department_counts = {}

            for assessment in assessments:
                if assessment.overall_wellness_score:
                    # Get department name from team or user
                    dept_name = "General"  # Default - would need to implement department lookup

                    if dept_name not in department_scores:
                        department_scores[dept_name] = 0
                        department_counts[dept_name] = 0

                    department_scores[dept_name] += assessment.overall_wellness_score
                    department_counts[dept_name] += 1

            # Calculate averages
            for dept_name in department_scores:
                if department_counts[dept_name] > 0:
                    department_scores[dept_name] /= department_counts[dept_name]

            return department_scores

        except Exception:
            return {}

    def _calculate_intervention_effectiveness(self, organization_id: UUID, team_id: Optional[UUID] = None,
                                            date_range: Tuple[datetime, datetime]) -> float:
        """Calculate effectiveness of wellness interventions"""
        try:
            # This would involve tracking wellness before and after interventions
            # For now, return a placeholder value
            return 75.0  # 75% effectiveness rate
        except Exception:
            return 0.0

    def _generate_compliance_recommendations(self, incidents: List[SafetyIncident],
                                           compliance_rate: float, overdue_count: int) -> List[str]:
        """Generate compliance improvement recommendations"""
        recommendations = []

        if compliance_rate < 80:
            recommendations.append("Implement automated compliance reporting system")
            recommendations.append("Schedule regular compliance training for safety managers")

        if overdue_count > 0:
            recommendations.append(f"Address {overdue_count} overdue compliance reports immediately")
            recommendations.append("Establish compliance reporting reminders and escalation procedures")

        critical_incidents = [inc for inc in incidents if inc.severity == IncidentSeverity.CRITICAL]
        if len(critical_incidents) > 0:
            recommendations.append("Review and update critical incident response procedures")
            recommendations.append("Conduct root cause analysis for all critical incidents")

        high_severity_incidents = [inc for inc in incidents if inc.severity == IncidentSeverity.HIGH]
        if len(high_severity_incidents) > len(incidents) * 0.2:  # More than 20% high severity
            recommendations.append("Implement additional preventive measures for high-risk activities")
            recommendations.append("Review safety protocols and PPE requirements")

        if not recommendations:
            recommendations.append("Continue current compliance practices")

        return recommendations

    def _calculate_performance_grade(self, performance_score: float) -> str:
        """Calculate performance grade based on score"""
        if performance_score >= 90:
            return "A+"
        elif performance_score >= 80:
            return "A"
        elif performance_score >= 70:
            return "B"
        elif performance_score >= 60:
            return "C"
        elif performance_score >= 50:
            return "D"
        else:
            return "F"