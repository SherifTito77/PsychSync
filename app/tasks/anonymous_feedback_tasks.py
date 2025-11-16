from celery import Celery
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import logging
from datetime import datetime, timedelta

from app.core.database import get_db
from app.services.email_service import email_service
from app.core.config import settings

celery_app = Celery('anonymous_feedback_tasks')
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

logger = logging.getLogger(__name__)


@celery_app.task(name="send_critical_feedback_alert")
def send_critical_feedback_alert(feedback_id: str) -> Dict[str, Any]:
    """
    Send immediate alerts for critical anonymous feedback

    This task is triggered automatically when critical severity feedback is submitted.
    It sends immediate notifications to HR leadership and safety officers.
    """
    try:
        db = next(get_db())

        # Get feedback details
        from app.db.models.anonymous_feedback import AnonymousFeedback
        from app.db.models.organization import Organization
        from app.db.models.user import User

        feedback = db.query(AnonymousFeedback).filter(
            AnonymousFeedback.id == feedback_id
        ).first()

        if not feedback:
            logger.error(f"Feedback not found: {feedback_id}")
            return {"success": False, "error": "Feedback not found"}

        # Get organization details
        organization = db.query(Organization).filter(
            Organization.id == feedback.organization_id
        ).first()

        # Get HR contacts for immediate notification
        hr_contacts = db.query(User).filter(
            User.organization_id == feedback.organization_id,
            User.is_active == True
        ).all()

        # Prepare email content
        severity_urgency = {
            'critical': 'IMMEDIATE ACTION REQUIRED',
            'high': 'HIGH PRIORITY'
        }

        email_subject = f"🚨 CRITICAL Anonymous Feedback Alert - {feedback.severity.upper()}"

        email_content = f"""
        IMMEDIATE ATTENTION REQUIRED

        Critical anonymous feedback has been submitted requiring immediate review:

        Type: {feedback.feedback_type}
        Category: {feedback.category}
        Severity: {feedback.severity.upper()}
        Submitted: {feedback.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

        Description Summary:
        {feedback.description[:200]}{'...' if len(feedback.description) > 200 else ''}

        Action Required:
        1. Login to review full details: {settings.FRONTEND_URL}/hr/anonymous-feedback
        2. Follow critical incident protocol
        3. Document all investigation steps
        4. Ensure immediate safety measures if needed

        This feedback was submitted completely anonymously to protect the reporter.
        All investigation must maintain confidentiality and avoid identification attempts.

        Urgency Level: {severity_urgency.get(feedback.severity, 'REVIEW REQUIRED')}
        Review Deadline: Within 24 hours
        """

        # Send alerts to HR contacts
        sent_count = 0
        for hr_contact in hr_contacts:
            try:
                email_service.send_email(
                    to_email=hr_contact.email,
                    subject=email_subject,
                    body=email_content,
                    template_name="critical_feedback_alert",
                    template_data={
                        "feedback": feedback,
                        "organization": organization,
                        "urgency_level": severity_urgency.get(feedback.severity),
                        "review_url": f"{settings.FRONTEND_URL}/hr/anonymous-feedback/{feedback.id}"
                    }
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send critical alert to {hr_contact.email}: {e}")

        # Log alert delivery
        logger.info(
            f"Critical feedback alert sent to {sent_count} HR contacts "
            f"for feedback {feedback_id} in org {feedback.organization_id}"
        )

        # Update feedback with alert sent flag
        feedback.auto_assigned = "true"  # Track that alerts were sent

        db.commit()

        return {
            "success": True,
            "feedback_id": feedback_id,
            "alerts_sent": sent_count,
            "severity": feedback.severity,
            "urgency_level": severity_urgency.get(feedback.severity)
        }

    except Exception as e:
        logger.error(f"Failed to send critical feedback alert: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="send_daily_feedback_digest")
def send_daily_feedback_digest(organization_id: str) -> Dict[str, Any]:
    """
    Send daily digest of pending anonymous feedback to HR

    This task runs daily to provide HR with a summary of feedback requiring review.
    """
    try:
        db = next(get_db())

        from app.db.models.anonymous_feedback import AnonymousFeedback
        from app.db.models.organization import Organization

        # Get yesterday's feedback
        yesterday = datetime.utcnow() - timedelta(days=1)
        start_of_day = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = yesterday.replace(hour=23, minute=59, second=59, microsecond=999999)

        feedbacks = db.query(AnonymousFeedback).filter(
            AnonymousFeedback.organization_id == organization_id,
            AnonymousFeedback.submitted_at >= start_of_day,
            AnonymousFeedback.submitted_at <= end_of_day
        ).all()

        if not feedbacks:
            logger.info(f"No new feedback for daily digest in org {organization_id}")
            return {"success": True, "message": "No new feedback to report"}

        # Get organization details
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        # Categorize feedback
        severity_counts = {}
        category_counts = {}
        pending_critical = []

        for feedback in feedbacks:
            # Count by severity
            severity_counts[feedback.severity] = severity_counts.get(feedback.severity, 0) + 1

            # Count by category
            category_counts[feedback.category] = category_counts.get(feedback.category, 0) + 1

            # Track critical items
            if feedback.severity in ['critical', 'high']:
                pending_critical.append({
                    'id': str(feedback.id),
                    'category': feedback.category,
                    'severity': feedback.severity,
                    'submitted_at': feedback.submitted_at.isoformat()
                })

        # Prepare email content
        email_subject = f"Daily Anonymous Feedback Digest - {organization.name}"

        email_content = f"""
        Daily Anonymous Feedback Summary for {organization.name}

        Total New Submissions: {len(feedbacks)}

        Severity Breakdown:
        """

        for severity, count in severity_counts.items():
            email_content += f"- {severity.title()}: {count}\n"

        email_content += "\nCategory Breakdown:\n"
        for category, count in category_counts.items():
            email_content += f"- {category.replace('_', ' ').title()}: {count}\n"

        if pending_critical:
            email_content += f"\n⚠️  High Priority Items Requiring Immediate Review ({len(pending_critical)}):\n"
            for item in pending_critical:
                email_content += f"- {item['category'].title()} ({item['severity'].upper()}) - Submitted {item['submitted_at']}\n"

        email_content += f"""

        Review Dashboard: {settings.FRONTEND_URL}/hr/anonymous-feedback

        Note: All feedback is completely anonymous. Focus on addressing issues, not identifying sources.
        """

        # Get HR contacts
        from app.db.models.user import User
        hr_contacts = db.query(User).filter(
            User.organization_id == organization_id,
            User.is_active == True
        ).all()

        # Send digest
        sent_count = 0
        for hr_contact in hr_contacts:
            try:
                email_service.send_email(
                    to_email=hr_contact.email,
                    subject=email_subject,
                    body=email_content,
                    template_name="daily_feedback_digest",
                    template_data={
                        "organization": organization,
                        "total_submissions": len(feedbacks),
                        "severity_counts": severity_counts,
                        "category_counts": category_counts,
                        "pending_critical": pending_critical,
                        "review_url": f"{settings.FRONTEND_URL}/hr/anonymous-feedback"
                    }
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send daily digest to {hr_contact.email}: {e}")

        logger.info(
            f"Daily feedback digest sent to {sent_count} HR contacts "
            f"for org {organization_id} - {len(feedbacks)} new submissions"
        )

        return {
            "success": True,
            "organization_id": organization_id,
            "total_submissions": len(feedbacks),
            "digest_sent": sent_count,
            "severity_breakdown": severity_counts,
            "critical_items": len(pending_critical)
        }

    except Exception as e:
        logger.error(f"Failed to send daily feedback digest: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="follow_up_on_pending_feedback")
def follow_up_on_pending_feedback() -> Dict[str, Any]:
    """
    Follow up on feedback pending beyond acceptable timeframes

    This task runs daily to identify and escalate feedback that has been pending too long.
    """
    try:
        db = next(get_db())

        from app.db.models.anonymous_feedback import AnonymousFeedback
        from datetime import timedelta

        # Define timeframes based on severity
        timeframes = {
            'critical': timedelta(hours=24),
            'high': timedelta(days=3),
            'medium': timedelta(days=7),
            'low': timedelta(days=14)
        }

        # Find overdue feedback
        overdue_feedbacks = []
        current_time = datetime.utcnow()

        for severity, timeframe in timeframes.items():
            cutoff_time = current_time - timeframe

            overdue = db.query(AnonymousFeedback).filter(
                AnonymousFeedback.severity == severity,
                AnonymousFeedback.status.in_(['pending_review', 'investigating']),
                AnonymousFeedback.submitted_at <= cutoff_time
            ).all()

            overdue_feedbacks.extend(overdue)

        if not overdue_feedbacks:
            return {"success": True, "message": "No overdue feedback found"}

        # Group by organization for reporting
        org_overdue = {}
        for feedback in overdue_feedbacks:
            org_id = str(feedback.organization_id)
            if org_id not in org_overdue:
                org_overdue[org_id] = []
            org_overdue[org_id].append(feedback)

        # Send escalation emails
        escalation_count = 0
        for org_id, feedbacks in org_overdue.items():
            try:
                # Get organization and HR contacts
                from app.db.models.organization import Organization
                from app.db.models.user import User

                organization = db.query(Organization).filter(
                    Organization.id == org_id
                ).first()

                hr_contacts = db.query(User).filter(
                    User.organization_id == org_id,
                    User.is_active == True
                ).all()

                # Prepare escalation email
                email_subject = f"⚠️ ESCALATION: Overdue Anonymous Feedback Review"

                email_content = f"""
                ESCALATION NOTICE

                The following anonymous feedback items are overdue for review:

                Total Overdue Items: {len(feedbacks)}

                """

                for feedback in feedbacks:
                    days_overdue = (current_time - feedback.submitted_at).days
                    email_content += f"""
                    - {feedback.category.title()} ({feedback.severity.upper()})
                      Severity: {feedback.severity}
                      Submitted: {feedback.submitted_at.strftime('%Y-%m-%d')}
                      Days Overdue: {days_overdue}
                      Status: {feedback.status}
                    """

                email_content += f"""

                Immediate Action Required:
                1. Review all overdue items immediately
                2. Update status and add investigation notes
                3. Escalate to senior leadership if needed

                Review Dashboard: {settings.FRONTEND_URL}/hr/anonymous-feedback

                This is an automated escalation due to missed review deadlines.
                """

                # Send escalation to HR contacts
                for hr_contact in hr_contacts:
                    try:
                        email_service.send_email(
                            to_email=hr_contact.email,
                            subject=email_subject,
                            body=email_content,
                            template_name="feedback_escalation",
                            template_data={
                                "organization": organization,
                                "overdue_count": len(feedbacks),
                                "feedbacks": feedbacks,
                                "review_url": f"{settings.FRONTEND_URL}/hr/anonymous-feedback"
                            }
                        )
                        escalation_count += 1
                    except Exception as e:
                        logger.error(f"Failed to send escalation to {hr_contact.email}: {e}")

            except Exception as e:
                logger.error(f"Failed to process escalation for org {org_id}: {e}")

        logger.info(
            f"Escalation notices sent for {len(overdue_feedbacks)} overdue items "
            f"across {len(org_overdue)} organizations"
        )

        return {
            "success": True,
            "overdue_items": len(overdue_feedbacks),
            "organizations_affected": len(org_overdue),
            "escalations_sent": escalation_count
        }

    except Exception as e:
        logger.error(f"Failed to process overdue feedback follow-up: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()


@celery_app.task(name="generate_monthly_anonymous_feedback_report")
def generate_monthly_anonymous_feedback_report(organization_id: str) -> Dict[str, Any]:
    """
    Generate monthly anonymous feedback analytics report

    This task generates comprehensive monthly reports for organizational leadership.
    """
    try:
        db = next(get_db())

        from app.services.anonymous_feedback_service import anonymous_feedback_service

        # Get monthly statistics
        stats = await anonymous_feedback_service.get_anonymous_feedback_statistics(
            db=db,
            organization_id=organization_id,
            days_back=30
        )

        # Get organization details
        from app.db.models.organization import Organization
        organization = db.query(Organization).filter(
            Organization.id == organization_id
        ).first()

        # Prepare monthly report
        report_data = {
            "organization": organization.name,
            "report_period": "Last 30 Days",
            "total_submissions": stats.get('total_submissions', 0),
            "psychological_safety_level": stats.get('insights', {}).get('psychological_safety_level', 'unknown'),
            "primary_concerns": stats.get('insights', {}).get('primary_concerns', []),
            "trending_issues": stats.get('insights', {}).get('trending_issues', []),
            "recommendations": stats.get('insights', {}).get('recommendations', []),
            "average_resolution_time": stats.get('average_resolution_time', 0),
            "benchmark_comparison": stats.get('benchmark_comparison', {})
        }

        # Send monthly report to leadership
        from app.db.models.user import User
        leadership_contacts = db.query(User).filter(
            User.organization_id == organization_id,
            User.is_active == True
        ).all()

        email_subject = f"Monthly Anonymous Feedback Report - {organization.name}"

        email_content = f"""
        Monthly Anonymous Feedback Report
        Organization: {organization.name}
        Period: Last 30 Days

        Executive Summary:
        - Total Anonymous Submissions: {report_data['total_submissions']}
        - Psychological Safety Level: {report_data['psychological_safety_level'].replace('_', ' ').title()}
        - Average Resolution Time: {report_data['average_resolution_time']} days

        Key Insights:
        {chr(10).join([f"- {concern['category']}: {concern['count']} reports" for concern in report_data['primary_concerns'][:3]])}

        Recommendations:
        {chr(10).join([f"- {rec}" for rec in report_data['recommendations'][:5]])}

        Full report available in the dashboard.
        """

        sent_count = 0
        for contact in leadership_contacts:
            try:
                email_service.send_email(
                    to_email=contact.email,
                    subject=email_subject,
                    body=email_content,
                    template_name="monthly_feedback_report",
                    template_data=report_data
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send monthly report to {contact.email}: {e}")

        logger.info(
            f"Monthly anonymous feedback report sent to {sent_count} leaders "
            f"for org {organization_id}"
        )

        return {
            "success": True,
            "organization_id": organization_id,
            "report_data": report_data,
            "reports_sent": sent_count
        }

    except Exception as e:
        logger.error(f"Failed to generate monthly feedback report: {e}")
        return {"success": False, "error": str(e)}
    finally:
        db.close()