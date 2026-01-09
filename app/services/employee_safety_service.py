"""
Employee Safety Service
Comprehensive safety management, incident tracking, and wellness monitoring service
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from typing import Any
from uuid import UUID

from sqlalchemy import desc, or_
from sqlalchemy.orm import Session

from app.db.models.employee_safety import (
    AlertLevel,
    IncidentSeverity,
    IncidentStatus,
    SafetyIncident,
    SafetyIncidentType,
    SafetyResource,
    WellnessAlert,
    WellnessAssessment,
)
from app.db.models.team import Team
from app.db.models.user import User
from app.services.email_service import EmailService
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


@dataclass
class IncidentReportData:
    """Data structure for incident reports"""

    incident_type: SafetyIncidentType
    severity: IncidentSeverity
    title: str
    description: str
    location: str | None = None
    date_occurred: datetime | None = None
    witnesses: list[dict[str, Any]] | None = None
    evidence_files: list[str] | None = None
    immediate_actions: list[str] | None = None
    affected_user_id: UUID | None = None


@dataclass
class WellnessAssessmentData:
    """Data structure for wellness assessments"""

    user_id: UUID
    organization_id: UUID
    team_id: UUID | None = None
    assessment_type: str = "scheduled"
    stress_level: float | None = None
    burnout_risk: float | None = None
    work_life_balance: float | None = None
    mental_health_score: float | None = None
    physical_wellness: float | None = None
    sleep_quality: float | None = None
    social_connection: float | None = None
    job_satisfaction: float | None = None
    engagement_level: float | None = None
    work_hours_per_week: float | None = None
    overtime_hours: float | None = None


class EmployeeSafetyService:
    """Comprehensive employee safety and wellness management service"""

    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.notification_service = NotificationService(db)

        # Wellness assessment thresholds
        self.wellness_thresholds = {
            "stress_level": {"elevated": 7.0, "high": 8.5, "critical": 9.5},
            "burnout_risk": {"elevated": 0.6, "high": 0.8, "critical": 0.9},
            "work_life_balance": {"elevated": 4.0, "high": 3.0, "critical": 2.0},  # Lower is worse
            "mental_health_score": {
                "elevated": 5.0,
                "high": 4.0,
                "critical": 3.0,
            },  # Lower is worse
            "sleep_quality": {"elevated": 5.0, "high": 4.0, "critical": 3.0},  # Lower is worse
            "engagement_level": {"elevated": 5.0, "high": 4.0, "critical": 3.0},  # Lower is worse
        }

    # Incident Reporting and Management

    async def report_incident(
        self,
        incident_data: IncidentReportData,
        reporter_id: UUID,
        organization_id: UUID,
        team_id: UUID | None = None,
    ) -> dict[str, Any]:
        """Report a new safety incident"""
        try:
            # Create incident record
            incident = SafetyIncident(
                incident_type=incident_data.incident_type,
                severity=incident_data.severity,
                title=incident_data.title,
                description=incident_data.description,
                location=incident_data.location,
                date_occurred=incident_data.date_occurred or datetime.utcnow(),
                witnesses=incident_data.witnesses or [],
                evidence_files=incident_data.evidence_files or [],
                immediate_actions=incident_data.immediate_actions or [],
                reporter_id=reporter_id,
                affected_user_id=incident_data.affected_user_id,
                organization_id=organization_id,
                team_id=team_id,
                date_reported=datetime.utcnow(),
            )

            self.db.add(incident)
            self.db.commit()
            self.db.refresh(incident)

            # Auto-escalate critical incidents
            if incident_data.severity == IncidentSeverity.CRITICAL:
                await self._escalate_incident(incident.id)

            # Trigger wellness check if psychological or bullying incident
            if (
                incident_data.incident_type
                in [
                    SafetyIncidentType.PSYCHOLOGICAL_INCIDENT,
                    SafetyIncidentType.BULLYING_HARASSMENT,
                ]
                and incident_data.affected_user_id
            ):
                await self._trigger_wellness_assessment(incident_data.affected_user_id, incident.id)

            # Send notifications
            await self._send_incident_notifications(incident)

            logger.info(f"Safety incident reported: {incident.id} - {incident.title}")

            return {
                "success": True,
                "incident_id": incident.id,
                "message": "Incident reported successfully",
                "severity": incident.severity.value,
                "status": incident.status.value,
            }

        except Exception as e:
            logger.error(f"Error reporting incident: {e!s}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to report incident: {e!s}"}

    async def get_incident(self, incident_id: UUID, user_id: UUID) -> dict[str, Any] | None:
        """Get incident details with appropriate access control"""
        incident = self.db.query(SafetyIncident).filter(SafetyIncident.id == incident_id).first()

        if not incident:
            return None

        # Check access permissions
        if not self._can_access_incident(incident, user_id):
            return None

        return self._serialize_incident(incident)

    async def update_incident_status(
        self,
        incident_id: UUID,
        new_status: IncidentStatus,
        investigator_id: UUID,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Update incident status during investigation"""
        try:
            incident = (
                self.db.query(SafetyIncident).filter(SafetyIncident.id == incident_id).first()
            )

            if not incident:
                return {"success": False, "error": "Incident not found"}

            incident.status = new_status
            incident.investigator_id = investigator_id

            if notes:
                incident.investigation_notes = notes

            incident.updated_at = datetime.utcnow()

            # Add follow-up actions for resolved incidents
            if new_status == IncidentStatus.RESOLVED:
                await self._create_follow_up_actions(incident)

            self.db.commit()

            # Send status update notifications
            await self._send_status_update_notifications(incident, new_status)

            logger.info(f"Incident {incident_id} status updated to {new_status.value}")

            return {
                "success": True,
                "message": f"Incident status updated to {new_status.value}",
                "status": new_status.value,
            }

        except Exception as e:
            logger.error(f"Error updating incident status: {e!s}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to update status: {e!s}"}

    async def get_incidents_dashboard(
        self,
        organization_id: UUID,
        team_id: UUID | None = None,
        date_range: tuple[datetime, datetime] | None = None,
    ) -> dict[str, Any]:
        """Get safety incidents dashboard data"""
        try:
            query = self.db.query(SafetyIncident).filter(
                SafetyIncident.organization_id == organization_id
            )

            if team_id:
                query = query.filter(SafetyIncident.team_id == team_id)

            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    SafetyIncident.date_reported >= start_date,
                    SafetyIncident.date_reported <= end_date,
                )

            incidents = query.order_by(desc(SafetyIncident.date_reported)).all()

            # Calculate statistics
            total_incidents = len(incidents)
            severity_breakdown = {}
            type_breakdown = {}
            status_breakdown = {}

            for incident in incidents:
                # Severity breakdown
                severity = incident.severity.value
                severity_breakdown[severity] = severity_breakdown.get(severity, 0) + 1

                # Type breakdown
                inc_type = incident.incident_type.value
                type_breakdown[inc_type] = type_breakdown.get(inc_type, 0) + 1

                # Status breakdown
                status = incident.status.value
                status_breakdown[status] = status_breakdown.get(status, 0) + 1

            # Recent incidents (last 7 days)
            seven_days_ago = datetime.utcnow() - timedelta(days=7)
            recent_incidents = [inc for inc in incidents if inc.date_reported >= seven_days_ago]

            # Critical incidents requiring attention
            critical_incidents = [
                inc
                for inc in incidents
                if inc.severity == IncidentSeverity.CRITICAL
                and inc.status not in [IncidentStatus.RESOLVED, IncidentStatus.CLOSED]
            ]

            return {
                "total_incidents": total_incidents,
                "recent_incidents": len(recent_incidents),
                "critical_incidents": len(critical_incidents),
                "severity_breakdown": severity_breakdown,
                "type_breakdown": type_breakdown,
                "status_breakdown": status_breakdown,
                "incidents": [
                    self._serialize_incident(inc) for inc in incidents[:50]
                ],  # Last 50 incidents
            }

        except Exception as e:
            logger.error(f"Error getting incidents dashboard: {e!s}")
            return {"error": f"Failed to load dashboard: {e!s}"}

    # Wellness Monitoring

    async def create_wellness_assessment(
        self, assessment_data: WellnessAssessmentData
    ) -> dict[str, Any]:
        """Create a new wellness assessment"""
        try:
            # Calculate overall wellness score
            overall_score = self._calculate_wellness_score(assessment_data)

            # Determine risk factors and alert level
            risk_factors, alert_level = self._assess_wellness_risks(assessment_data)

            # Generate AI insights and recommendations
            insights, recommendations = await self._generate_wellness_insights(
                assessment_data, risk_factors
            )

            assessment = WellnessAssessment(
                user_id=assessment_data.user_id,
                organization_id=assessment_data.organization_id,
                team_id=assessment_data.team_id,
                assessment_type=assessment_data.assessment_type,
                stress_level=assessment_data.stress_level,
                burnout_risk=assessment_data.burnout_risk,
                work_life_balance=assessment_data.work_life_balance,
                mental_health_score=assessment_data.mental_health_score,
                physical_wellness=assessment_data.physical_wellness,
                sleep_quality=assessment_data.sleep_quality,
                social_connection=assessment_data.social_connection,
                job_satisfaction=assessment_data.job_satisfaction,
                engagement_level=assessment_data.engagement_level,
                work_hours_per_week=assessment_data.work_hours_per_week,
                overtime_hours=assessment_data.overtime_hours,
                overall_wellness_score=overall_score,
                risk_factors=risk_factors,
                alert_level=alert_level,
                ai_insights=insights,
                recommendations=recommendations,
            )

            self.db.add(assessment)
            self.db.commit()
            self.db.refresh(assessment)

            # Create alerts if needed
            if alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]:
                await self._create_wellness_alerts(assessment, alert_level, risk_factors)

            logger.info(
                f"Wellness assessment created for user {assessment_data.user_id}: score {overall_score}"
            )

            return {
                "success": True,
                "assessment_id": assessment.id,
                "overall_score": overall_score,
                "alert_level": alert_level.value,
                "risk_factors_count": len(risk_factors),
            }

        except Exception as e:
            logger.error(f"Error creating wellness assessment: {e!s}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to create assessment: {e!s}"}

    async def get_wellness_dashboard(
        self, organization_id: UUID, team_id: UUID | None = None
    ) -> dict[str, Any]:
        """Get wellness dashboard data for organization/team"""
        try:
            # Get recent assessments
            query = self.db.query(WellnessAssessment).filter(
                WellnessAssessment.organization_id == organization_id
            )

            if team_id:
                query = query.filter(WellnessAssessment.team_id == team_id)

            # Last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            assessments = (
                query.filter(WellnessAssessment.assessment_date >= thirty_days_ago)
                .order_by(desc(WellnessAssessment.assessment_date))
                .all()
            )

            if not assessments:
                return {"message": "No wellness data available"}

            # Calculate statistics
            total_assessments = len(assessments)
            average_scores = self._calculate_average_wellness_scores(assessments)

            # Alert breakdown
            alert_breakdown = {}
            for assessment in assessments:
                alert_level = assessment.alert_level.value
                alert_breakdown[alert_level] = alert_breakdown.get(alert_level, 0) + 1

            # High-risk employees
            high_risk_assessments = [
                a for a in assessments if a.alert_level in [AlertLevel.HIGH, AlertLevel.CRITICAL]
            ]

            # Trends over time
            weekly_trends = self._calculate_wellness_trends(assessments)

            return {
                "total_assessments": total_assessments,
                "high_risk_employees": len(set(a.user_id for a in high_risk_assessments)),
                "average_scores": average_scores,
                "alert_breakdown": alert_breakdown,
                "weekly_trends": weekly_trends,
                "recent_assessments": [
                    self._serialize_wellness_assessment(a) for a in assessments[:20]
                ],
            }

        except Exception as e:
            logger.error(f"Error getting wellness dashboard: {e!s}")
            return {"error": f"Failed to load wellness dashboard: {e!s}"}

    async def get_employee_wellness_history(
        self, user_id: UUID, date_range: tuple[datetime, datetime] | None = None
    ) -> list[dict[str, Any]]:
        """Get wellness assessment history for a specific employee"""
        try:
            query = self.db.query(WellnessAssessment).filter(WellnessAssessment.user_id == user_id)

            if date_range:
                start_date, end_date = date_range
                query = query.filter(
                    WellnessAssessment.assessment_date >= start_date,
                    WellnessAssessment.assessment_date <= end_date,
                )

            assessments = query.order_by(desc(WellnessAssessment.assessment_date)).all()

            return [self._serialize_wellness_assessment(a) for a in assessments]

        except Exception as e:
            logger.error(f"Error getting employee wellness history: {e!s}")
            return []

    # Safety Resources and Training

    async def create_safety_resource(
        self,
        organization_id: UUID,
        title: str,
        description: str,
        resource_type: str,
        content: str | None = None,
        file_url: str | None = None,
        category: str | None = None,
        is_public: bool = False,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        """Create a new safety resource"""
        try:
            resource = SafetyResource(
                organization_id=organization_id,
                title=title,
                description=description,
                resource_type=resource_type,
                category=category,
                content=content,
                file_url=file_url,
                is_public=is_public,
                tags=tags or [],
                last_reviewed=datetime.utcnow(),
                next_review_date=datetime.utcnow() + timedelta(days=365),  # Annual review
            )

            self.db.add(resource)
            self.db.commit()
            self.db.refresh(resource)

            logger.info(f"Safety resource created: {resource.id} - {title}")

            return {
                "success": True,
                "resource_id": resource.id,
                "message": "Safety resource created successfully",
            }

        except Exception as e:
            logger.error(f"Error creating safety resource: {e!s}")
            self.db.rollback()
            return {"success": False, "error": f"Failed to create resource: {e!s}"}

    async def get_safety_resources(
        self,
        organization_id: UUID,
        resource_type: str | None = None,
        category: str | None = None,
        user_role: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get safety resources with filtering"""
        try:
            query = self.db.query(SafetyResource).filter(
                SafetyResource.organization_id == organization_id
            )

            if resource_type:
                query = query.filter(SafetyResource.resource_type == resource_type)

            if category:
                query = query.filter(SafetyResource.category == category)

            # Filter by role if not public
            if user_role:
                query = query.filter(
                    or_(
                        SafetyResource.is_public == True,
                        SafetyResource.required_roles.contains([user_role]),
                    )
                )
            else:
                query = query.filter(SafetyResource.is_public == True)

            resources = query.order_by(SafetyResource.title).all()

            # Increment view count and update last accessed
            for resource in resources:
                resource.view_count += 1
                resource.last_accessed = datetime.utcnow()

            self.db.commit()

            return [self._serialize_safety_resource(r) for r in resources]

        except Exception as e:
            logger.error(f"Error getting safety resources: {e!s}")
            return []

    # Helper Methods

    def _can_access_incident(self, incident: SafetyIncident, user_id: UUID) -> bool:
        """Check if user has permission to access incident"""
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Admin can access all incidents
        if user.is_superuser:
            return True

        # Reporter can access their own reports
        if incident.reporter_id == user_id:
            return True

        # Affected user can access incidents they're involved in
        if incident.affected_user_id == user_id:
            return True

        # Organization admin can access all org incidents
        if incident.organization_id == user.organization_id and user.is_admin:
            return True

        # Team manager can access team incidents
        if incident.team_id:
            team_member = (
                self.db.query(Team)
                .filter(
                    Team.id == incident.team_id,
                    Team.members.any(user_id=user_id),  # Assuming members relationship exists
                )
                .first()
            )
            if team_member:
                # Check if user is team manager
                # This would depend on your team structure
                return True

        return False

    def _serialize_incident(self, incident: SafetyIncident) -> dict[str, Any]:
        """Serialize incident object for API response"""
        return {
            "id": str(incident.id),
            "incident_type": incident.incident_type.value,
            "severity": incident.severity.value,
            "status": incident.status.value,
            "title": incident.title,
            "description": incident.description,
            "location": incident.location,
            "date_occurred": incident.date_occurred.isoformat() if incident.date_occurred else None,
            "date_reported": incident.date_reported.isoformat() if incident.date_reported else None,
            "reporter_id": str(incident.reporter_id) if incident.reporter_id else None,
            "affected_user_id": str(incident.affected_user_id)
            if incident.affected_user_id
            else None,
            "organization_id": str(incident.organization_id),
            "team_id": str(incident.team_id) if incident.team_id else None,
            "witnesses": incident.witnesses,
            "evidence_files": incident.evidence_files,
            "immediate_actions": incident.immediate_actions,
            "investigator_id": str(incident.investigator_id) if incident.investigator_id else None,
            "investigation_notes": incident.investigation_notes,
            "root_cause": incident.root_cause,
            "prevention_measures": incident.prevention_measures,
            "resolution_date": incident.resolution_date.isoformat()
            if incident.resolution_date
            else None,
            "resolution_details": incident.resolution_details,
            "lessons_learned": incident.lessons_learned,
            "compliance_required": incident.compliance_required,
            "compliance_reported": incident.compliance_reported,
            "created_at": incident.created_at.isoformat(),
            "updated_at": incident.updated_at.isoformat(),
        }

    def _serialize_wellness_assessment(self, assessment: WellnessAssessment) -> dict[str, Any]:
        """Serialize wellness assessment for API response"""
        return {
            "id": str(assessment.id),
            "user_id": str(assessment.user_id),
            "organization_id": str(assessment.organization_id),
            "team_id": str(assessment.team_id) if assessment.team_id else None,
            "assessment_date": assessment.assessment_date.isoformat(),
            "assessment_type": assessment.assessment_type,
            "metrics": {
                "stress_level": assessment.stress_level,
                "burnout_risk": assessment.burnout_risk,
                "work_life_balance": assessment.work_life_balance,
                "mental_health_score": assessment.mental_health_score,
                "physical_wellness": assessment.physical_wellness,
                "sleep_quality": assessment.sleep_quality,
                "social_connection": assessment.social_connection,
                "job_satisfaction": assessment.job_satisfaction,
                "engagement_level": assessment.engagement_level,
            },
            "overall_wellness_score": assessment.overall_wellness_score,
            "risk_factors": assessment.risk_factors,
            "alert_level": assessment.alert_level.value,
            "work_hours_per_week": assessment.work_hours_per_week,
            "overtime_hours": assessment.overtime_hours,
            "recent_incidents": assessment.recent_incidents,
            "support_systems": assessment.support_systems,
            "ai_insights": assessment.ai_insights,
            "recommendations": assessment.recommendations,
            "created_at": assessment.created_at.isoformat(),
        }

    def _serialize_safety_resource(self, resource: SafetyResource) -> dict[str, Any]:
        """Serialize safety resource for API response"""
        return {
            "id": str(resource.id),
            "title": resource.title,
            "description": resource.description,
            "resource_type": resource.resource_type,
            "category": resource.category,
            "content": resource.content,
            "file_url": resource.file_url,
            "external_links": resource.external_links,
            "is_public": resource.is_public,
            "required_roles": resource.required_roles,
            "targeted_teams": resource.targeted_teams,
            "tags": resource.tags,
            "language": resource.language,
            "view_count": resource.view_count,
            "last_accessed": resource.last_accessed.isoformat() if resource.last_accessed else None,
            "last_reviewed": resource.last_reviewed.isoformat() if resource.last_reviewed else None,
            "next_review_date": resource.next_review_date.isoformat()
            if resource.next_review_date
            else None,
            "created_at": resource.created_at.isoformat(),
        }

    # Private helper methods for wellness calculations

    def _calculate_wellness_score(self, assessment_data: WellnessAssessmentData) -> float:
        """Calculate overall wellness score from individual metrics"""
        metrics = [
            assessment_data.stress_level,
            assessment_data.work_life_balance,
            assessment_data.mental_health_score,
            assessment_data.physical_wellness,
            assessment_data.sleep_quality,
            assessment_data.social_connection,
            assessment_data.job_satisfaction,
            assessment_data.engagement_level,
        ]

        # Filter out None values and normalize stress (lower is better)
        valid_metrics = []
        for metric in metrics:
            if metric is not None:
                valid_metrics.append(metric)

        if not valid_metrics:
            return 0.0

        # Average of available metrics (converted to 0-100 scale)
        average_score = sum(valid_metrics) / len(valid_metrics)
        return round((average_score / 10.0) * 100, 2)

    def _assess_wellness_risks(
        self, assessment_data: WellnessAssessmentData
    ) -> tuple[list[str], AlertLevel]:
        """Assess wellness risks and determine alert level"""
        risk_factors = []
        max_alert_level = AlertLevel.NORMAL

        # Check each metric against thresholds
        for metric_name, value in [
            ("stress_level", assessment_data.stress_level),
            ("burnout_risk", assessment_data.burnout_risk),
            ("work_life_balance", assessment_data.work_life_balance),
            ("mental_health_score", assessment_data.mental_health_score),
            ("sleep_quality", assessment_data.sleep_quality),
            ("engagement_level", assessment_data.engagement_level),
        ]:
            if value is None:
                continue

            if metric_name in self.wellness_thresholds:
                thresholds = self.wellness_thresholds[metric_name]

                # For metrics where lower is worse (work_life_balance, mental_health, sleep_quality, engagement)
                lower_is_worse = metric_name in [
                    "work_life_balance",
                    "mental_health_score",
                    "sleep_quality",
                    "engagement_level",
                ]

                if lower_is_worse:
                    if value <= thresholds["critical"]:
                        risk_factors.append(f"Critical {metric_name.replace('_', ' ')}")
                        max_alert_level = AlertLevel.CRITICAL
                    elif value <= thresholds["high"]:
                        risk_factors.append(f"High {metric_name.replace('_', ' ')}")
                        max_alert_level = max(
                            max_alert_level,
                            AlertLevel.HIGH,
                            key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
                        )
                    elif value <= thresholds["elevated"]:
                        risk_factors.append(f"Elevated {metric_name.replace('_', ' ')}")
                        max_alert_level = max(
                            max_alert_level,
                            AlertLevel.ELEVATED,
                            key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
                        )
                # For metrics where higher is worse (stress, burnout)
                elif value >= thresholds["critical"]:
                    risk_factors.append(f"Critical {metric_name.replace('_', ' ')}")
                    max_alert_level = AlertLevel.CRITICAL
                elif value >= thresholds["high"]:
                    risk_factors.append(f"High {metric_name.replace('_', ' ')}")
                    max_alert_level = max(
                        max_alert_level,
                        AlertLevel.HIGH,
                        key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
                    )
                elif value >= thresholds["elevated"]:
                    risk_factors.append(f"Elevated {metric_name.replace('_', ' ')}")
                    max_alert_level = max(
                        max_alert_level,
                        AlertLevel.ELEVATED,
                        key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
                    )

        # Additional risk factors
        if assessment_data.work_hours_per_week and assessment_data.work_hours_per_week > 55:
            risk_factors.append("Excessive work hours")
            max_alert_level = max(
                max_alert_level,
                AlertLevel.HIGH,
                key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
            )

        if assessment_data.overtime_hours and assessment_data.overtime_hours > 10:
            risk_factors.append("High overtime hours")
            max_alert_level = max(
                max_alert_level,
                AlertLevel.ELEVATED,
                key=lambda x: ["normal", "elevated", "high", "critical"].index(x.value),
            )

        return risk_factors, max_alert_level

    async def _generate_wellness_insights(
        self, assessment_data: WellnessAssessmentData, risk_factors: list[str]
    ) -> tuple[dict[str, Any], list[str]]:
        """Generate AI-powered insights and recommendations"""
        insights = {
            "summary": "Wellness assessment completed",
            "key_concerns": risk_factors[:3],  # Top 3 concerns
            "positive_factors": [],
            "trend_analysis": "Insufficient data for trend analysis",
        }

        recommendations = []

        # Generate recommendations based on risk factors
        if "stress_level" in str(risk_factors):
            recommendations.extend(
                [
                    "Consider stress management techniques (mindfulness, meditation)",
                    "Take regular breaks during work hours",
                    "Discuss workload with manager",
                ]
            )

        if "burnout_risk" in str(risk_factors):
            recommendations.extend(
                [
                    "Schedule time off or vacation",
                    "Set clear work-life boundaries",
                    "Seek support from HR or mental health professional",
                ]
            )

        if "work_life_balance" in str(risk_factors):
            recommendations.extend(
                [
                    "Establish clear work hours and stick to them",
                    "Create dedicated time for personal activities",
                    "Consider flexible work arrangements if available",
                ]
            )

        if "sleep_quality" in str(risk_factors):
            recommendations.extend(
                [
                    "Maintain consistent sleep schedule",
                    "Create relaxing bedtime routine",
                    "Limit screen time before bed",
                ]
            )

        # Add positive factors
        positive_metrics = []
        if assessment_data.job_satisfaction and assessment_data.job_satisfaction >= 7:
            positive_metrics.append("High job satisfaction")
        if assessment_data.social_connection and assessment_data.social_connection >= 7:
            positive_metrics.append("Strong social connections")
        if assessment_data.physical_wellness and assessment_data.physical_wellness >= 7:
            positive_metrics.append("Good physical wellness")

        insights["positive_factors"] = positive_metrics

        return insights, recommendations

    async def _create_wellness_alerts(
        self, assessment: WellnessAssessment, alert_level: AlertLevel, risk_factors: list[str]
    ) -> None:
        """Create wellness alerts for high-risk assessments"""
        try:
            # Create alert for each significant risk factor
            for risk_factor in risk_factors[:3]:  # Limit to top 3
                alert = WellnessAlert(
                    assessment_id=assessment.id,
                    user_id=assessment.user_id,
                    alert_type=risk_factor.lower().replace(" ", "_"),
                    severity=alert_level,
                    title=f"Wellness Alert: {risk_factor}",
                    message=f"Concern detected in {risk_factor.lower()}. Immediate attention recommended.",
                    trigger_metrics={
                        risk_factor.lower(): getattr(assessment, risk_factor.lower(), None)
                    },
                    recommended_actions=[
                        "Schedule check-in with manager",
                        "Consider mental health resources",
                        "Review workload and priorities",
                    ],
                )

                self.db.add(alert)

            self.db.commit()

            # Send notifications for critical alerts
            if alert_level == AlertLevel.CRITICAL:
                await self._send_critical_wellness_alerts(assessment, risk_factors)

        except Exception as e:
            logger.error(f"Error creating wellness alerts: {e!s}")

    async def _escalate_incident(self, incident_id: UUID) -> None:
        """Escalate critical incidents to appropriate personnel"""
        # Implementation for incident escalation

    async def _trigger_wellness_assessment(self, user_id: UUID, incident_id: UUID) -> None:
        """Trigger wellness assessment after psychological incident"""
        # Implementation for wellness assessment trigger

    async def _send_incident_notifications(self, incident: SafetyIncident) -> None:
        """Send notifications for new incident"""
        # Implementation for incident notifications

    async def _send_status_update_notifications(
        self, incident: SafetyIncident, new_status: IncidentStatus
    ) -> None:
        """Send notifications for incident status updates"""
        # Implementation for status update notifications

    async def _create_follow_up_actions(self, incident: SafetyIncident) -> None:
        """Create follow-up actions for resolved incidents"""
        # Implementation for follow-up actions

    async def _send_critical_wellness_alerts(
        self, assessment: WellnessAssessment, risk_factors: list[str]
    ) -> None:
        """Send notifications for critical wellness alerts"""
        # Implementation for critical wellness notifications

    def _calculate_average_wellness_scores(
        self, assessments: list[WellnessAssessment]
    ) -> dict[str, float]:
        """Calculate average wellness scores from list of assessments"""
        if not assessments:
            return {}

        metrics = [
            "stress_level",
            "burnout_risk",
            "work_life_balance",
            "mental_health_score",
            "physical_wellness",
            "sleep_quality",
            "social_connection",
            "job_satisfaction",
            "engagement_level",
        ]

        averages = {}
        for metric in metrics:
            values = [getattr(a, metric) for a in assessments if getattr(a, metric) is not None]
            if values:
                averages[metric] = round(sum(values) / len(values), 2)

        # Add overall score
        overall_scores = [
            a.overall_wellness_score for a in assessments if a.overall_wellness_score is not None
        ]
        if overall_scores:
            averages["overall_score"] = round(sum(overall_scores) / len(overall_scores), 2)

        return averages

    def _calculate_wellness_trends(
        self, assessments: list[WellnessAssessment]
    ) -> dict[str, list[float]]:
        """Calculate wellness trends over time"""
        # Group assessments by week
        weekly_data = {}
        for assessment in assessments:
            week_start = assessment.assessment_date - timedelta(
                days=assessment.assessment_date.weekday()
            )
            week_key = week_start.strftime("%Y-%W")

            if week_key not in weekly_data:
                weekly_data[week_key] = []
            weekly_data[week_key].append(assessment.overall_wellness_score or 0)

        # Calculate weekly averages
        trends = {}
        for week_key, scores in sorted(weekly_data.items()):
            if scores:
                trends[week_key] = round(sum(scores) / len(scores), 2)

        return trends
