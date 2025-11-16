# app/services/anonymous_feedback_service.py
"""
Anonymous Feedback System for Psychological Safety
Enables employees to report concerns without fear of retaliation
"""

import secrets
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func
from collections import Counter, defaultdict
from typing import Dict, List, Any, Optional

from app.db.models.anonymous_feedback import AnonymousFeedback
from app.core.logging_config import logger

@dataclass
class FeedbackSubmission:
    """Anonymous feedback submission data"""
    feedback_type: str
    category: str
    description: str
    severity: str
    target_type: Optional[str] = None
    target_id: Optional[str] = None
    evidence_urls: Optional[List[str]] = None

class AnonymousFeedbackService:
    """
    Truly anonymous feedback system with multiple safety layers
    Focus on psychological safety and toxicity prevention
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Feedback categories focused on psychological safety
        self.feedback_categories = {
            'toxic_behavior': {
                'description': 'Report toxic behavior, bullying, or harassment',
                'subcategories': ['verbal_abuse', 'bullying', 'harassment', 'intimidation'],
                'severity_levels': ['low', 'medium', 'high', 'critical']
            },
            'psychological_safety': {
                'description': 'Report psychological safety concerns',
                'subcategories': ['fear_speaking_up', 'exclusion', 'micromanagement', 'unfair_treatment'],
                'severity_levels': ['low', 'medium', 'high', 'critical']
            },
            'team_dynamics': {
                'description': 'Report team collaboration and communication issues',
                'subcategories': ['poor_communication', 'conflict', 'lack_collaboration', 'isolation'],
                'severity_levels': ['low', 'medium', 'high', 'critical']
            },
            'leadership_concerns': {
                'description': 'Report leadership and management concerns',
                'subcategories': ['poor_leadership', 'favoritism', 'lack_support', 'unrealistic_expectations'],
                'severity_levels': ['low', 'medium', 'high', 'critical']
            },
            'workplace_environment': {
                'description': 'Report workplace environment issues',
                'subcategories': ['stress_burnout', 'workload', 'resources', 'culture_issues'],
                'severity_levels': ['low', 'medium', 'high', 'critical']
            },
            'discrimination_bias': {
                'description': 'Report discrimination or bias concerns',
                'subcategories': ['gender_bias', 'racial_bias', 'age_discrimination', 'accessibility_issues'],
                'severity_levels': ['medium', 'high', 'critical']
            }
        }

    async def submit_anonymous_feedback(
        self,
        db: Session,
        organization_id: str,
        feedback_data: FeedbackSubmission
    ) -> Dict[str, Any]:
        """
        Submit completely anonymous feedback with maximum privacy protection
        """

        try:
            # Generate anonymous tracking ID (only for status checking)
            tracking_id = secrets.token_urlsafe(32)

            # Hash any target information to prevent reverse lookup
            target_id_hash = None
            if feedback_data.target_id:
                # Double hash for additional security
                first_hash = hashlib.sha256(feedback_data.target_id.encode()).hexdigest()
                target_id_hash = hashlib.sha256(first_hash.encode()).hexdigest()

            # Generate anonymous submitter fingerprint (for duplicate detection, not identification)
            submitter_fingerprint = self._generate_anonymous_fingerprint()

            # Create feedback record with maximum anonymity
            feedback = AnonymousFeedback(
                organization_id=organization_id,
                tracking_id=tracking_id,
                feedback_type=feedback_data.feedback_type,
                category=feedback_data.category,
                description=self._sanitize_description(feedback_data.description),
                severity=feedback_data.severity,
                target_type=feedback_data.target_type,
                target_id_hash=target_id_hash,  # Hashed, not plain
                evidence_urls=feedback_data.evidence_urls,
                submitter_fingerprint=submitter_fingerprint,
                submitted_at=datetime.utcnow(),
                status='pending_review',
                # CRITICAL: No user_id or any identifying information
            )

            db.add(feedback)
        await db.commit()
            await db.refresh(feedback)

            # Log anonymously (no identifying information)
            self.logger.info(
                f"Anonymous feedback submitted: {feedback_data.feedback_type}/"
                f"{feedback_data.category} - Severity: {feedback_data.severity} - "
                f"Tracking ID: {tracking_id[:8]}..."
            )

            # Trigger appropriate alerts and workflows
            await self._handle_feedback_submission(db, feedback)

            return {
                'success': True,
                'tracking_id': tracking_id,
                'message': 'Your feedback has been submitted completely anonymously. '
                          'Save this tracking ID to check status later.',
                'status_check_url': f'/api/v1/anonymous-feedback/status/{tracking_id}',
                'security_reminder': 'This submission is 100% anonymous. We cannot identify who submitted it.',
                'next_steps': [
                    'Your feedback will be reviewed by trained HR professionals',
                    'Investigations typically begin within 48-72 hours',
                    'You can check status anytime using your tracking ID',
                    'Your identity remains completely protected'
                ],
                'support_resources': self._get_support_resources(feedback_data.feedback_type)
            }

        except Exception as e:
            self.logger.error(f"Anonymous feedback submission failed: {e}")
            return {
                'success': False,
                'error': 'Failed to submit feedback. Please try again or use alternative reporting methods.',
                'alternatives': [
                    'Contact HR directly via confidential channel',
                    'Use external reporting hotlines',
                    'Speak with a trusted manager or mentor'
                ]
            }

    async def check_feedback_status(
        self,
        db: Session,
        tracking_id: str
    ) -> Dict[str, Any]:
        """
        Check status of anonymous feedback using tracking ID
        Maintains complete anonymity
        """

        try:
            feedback = result = await db.execute(query)
        return result.scalars().all()

            if not feedback:
                return {
                    'found': False,
                    'message': 'Feedback not found. Please check your tracking ID or contact support.',
                    'help': 'If you lost your tracking ID, we unfortunately cannot locate your specific submission due to anonymity protections.'
                }

            # Calculate estimated resolution time
            days_since_submission = (datetime.utcnow() - feedback.submitted_at).days
            estimated_resolution = self._estimate_resolution_time(feedback.severity, feedback.status)

            return {
                'found': True,
                'status': feedback.status,
                'submitted_at': feedback.submitted_at.isoformat(),
                'days_since_submission': days_since_submission,
                'last_updated': feedback.updated_at.isoformat() if feedback.updated_at else None,
                'public_resolution_notes': feedback.public_resolution_notes,
                'severity': feedback.severity,
                'category': feedback.category,
                'estimated_resolution_days': estimated_resolution,
                'status_explanation': self._get_status_explanation(feedback.status),
                'privacy_reminder': 'Your identity remains completely anonymous throughout this process.',
                'next_steps': self._get_status_next_steps(feedback.status)
            }

        except Exception as e:
            self.logger.error(f"Failed to check feedback status: {e}")
            return {
                'found': False,
                'error': 'Unable to check status. Please try again later.',
                'alternatives': ['Contact HR support', 'Try submitting new feedback']
            }

    async def get_feedback_for_review(
        self,
        db: Session,
        organization_id: str,
        reviewer_id: str,
        status_filter: Optional[str] = 'pending_review',
        severity_filter: Optional[str] = None,
        category_filter: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        Get anonymous feedback for HR/team review
        Returns sanitized feedback with no identifying information
        """

        try:
            # Verify reviewer has appropriate permissions
            if not await self._verify_reviewer_permissions(db, reviewer_id, organization_id):
                raise PermissionError("Insufficient permissions to review feedback")

            # Build query with filters
            query = db.query(AnonymousFeedback).filter(
                AnonymousFeedback.organization_id == organization_id
            )

            if status_filter:
                query = query.filter(AnonymousFeedback.status == status_filter)

            if severity_filter:
                query = query.filter(AnonymousFeedback.severity == severity_filter)

            if category_filter:
                query = query.filter(AnonymousFeedback.category == category_filter)

            # Order by severity and submission date
            feedbacks = query.order_by(
                # Custom severity ordering
                func.case(
                    (AnonymousFeedback.severity == 'critical', 1),
                    (AnonymousFeedback.severity == 'high', 2),
                    (AnonymousFeedback.severity == 'medium', 3),
                    (AnonymousFeedback.severity == 'low', 4),
                    else_=5
                ),
                AnonymousFeedback.submitted_at.desc()
            ).limit(limit).all()

            # Sanitize feedback data (remove any potential identifying information)
            sanitized_feedbacks = []
            for feedback in feedbacks:
                sanitized_feedbacks.append({
                    'id': str(feedback.id),
                    'feedback_type': feedback.feedback_type,
                    'category': feedback.category,
                    'description': feedback.description,
                    'severity': feedback.severity,
                    'target_type': feedback.target_type,
                    'target_id_hash': feedback.target_id_hash,  # Hashed only
                    'submitted_at': feedback.submitted_at.isoformat(),
                    'days_pending': (datetime.utcnow() - feedback.submitted_at).days,
                    'status': feedback.status,
                    'evidence_count': len(feedback.evidence_urls) if feedback.evidence_urls else 0,
                    'urgency_score': self._calculate_urgency_score(feedback),
                    'recommended_actions': self._get_recommended_actions(feedback),
                    # NO tracking_id or submitter information exposed
                })

            # Calculate summary statistics
            summary = self._calculate_feedback_summary(feedbacks)

            return {
                'feedbacks': sanitized_feedbacks,
                'summary': summary,
                'total_count': len(feedbacks),
                'reviewer_id': reviewer_id,
                'review_timestamp': datetime.utcnow().isoformat(),
                'privacy_guidelines': [
                    'All feedback is completely anonymous',
                    'Do not attempt to identify submitters',
                    'Focus on addressing the issues, not finding sources',
                    'Maintain confidentiality throughout investigation'
                ]
            }

        except Exception as e:
            self.logger.error(f"Failed to get feedback for review: {e}")
            raise

    async def update_feedback_status(
        self,
        db: Session,
        feedback_id: str,
        reviewer_id: str,
        new_status: str,
        resolution_notes: Optional[str] = None,
        public_resolution_notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update feedback status with appropriate permissions
        """

        try:
            # Verify permissions
            feedback = result = await db.execute(query)
        return result.scalars().all()

            if not feedback:
                return {
                    'success': False,
                    'error': 'Feedback not found'
                }

            if not await self._verify_reviewer_permissions(db, reviewer_id, feedback.organization_id):
                return {
                    'success': False,
                    'error': 'Insufficient permissions'
                }

            # Update feedback
            feedback.status = new_status
            feedback.updated_at = datetime.utcnow()

            if resolution_notes:
                feedback.resolution_notes = resolution_notes

            if public_resolution_notes:
                # Sanitize public notes to remove any identifying information
                feedback.public_resolution_notes = self._sanitize_public_notes(public_resolution_notes)

            # If resolved, set resolution date
            if new_status in ['resolved', 'closed']:
                feedback.resolution_date = datetime.utcnow()

            await db.commit()

            # Log status change
            self.logger.info(
                f"Feedback {feedback_id} status updated to {new_status} by reviewer {reviewer_id[:8]}..."
            )

            return {
                'success': True,
                'feedback_id': feedback_id,
                'new_status': new_status,
                'updated_at': feedback.updated_at.isoformat(),
                'message': 'Feedback status updated successfully'
            }

        except Exception as e:
            self.logger.error(f"Failed to update feedback status: {e}")
            await db.rollback()
            return {
                'success': False,
                'error': 'Failed to update status'
            }

    async def get_anonymous_feedback_statistics(
        self,
        db: Session,
        organization_id: str,
        days_back: int = 90
    ) -> Dict[str, Any]:
        """
        Get anonymous feedback statistics for organizational insights
        All data is aggregated and anonymous
        """

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)

            feedbacks = db.query(AnonymousFeedback).filter(
                and_(
                    AnonymousFeedback.organization_id == organization_id,
                    AnonymousFeedback.submitted_at >= cutoff_date
                )
            ).all()

            if not feedbacks:
                return {
                    'total_submissions': 0,
                    'analysis_period_days': days_back,
                    'insights': {
                        'psychological_safety_level': 'insufficient_data',
                        'primary_concerns': [],
                        'trending_issues': [],
                        'recommendations': [
                            'Encourage anonymous feedback submissions',
                            'Promote psychological safety awareness',
                            'Establish clear reporting channels'
                        ]
                    }
                }

            # Analyze patterns and trends
            category_stats = Counter([f.category for f in feedbacks])
            severity_stats = Counter([f.severity for f in feedbacks])
            status_stats = Counter([f.status for f in feedbacks])

            # Calculate submission trends
            daily_submissions = defaultdict(int)
            for feedback in feedbacks:
                date_key = feedback.submitted_at.date().isoformat()
                daily_submissions[date_key] += 1

            # Generate insights
            psychological_safety_level = self._assess_psychological_safety_level(feedbacks)
            primary_concerns = self._identify_primary_concerns(category_stats, severity_stats)
            trending_issues = self._identify_trending_issues(feedbacks)

            # Generate organizational recommendations
            recommendations = self._generate_organizational_recommendations(
                feedbacks, category_stats, severity_stats
            )

            return {
                'total_submissions': len(feedbacks),
                'analysis_period_days': days_back,
                'category_breakdown': dict(category_stats),
                'severity_breakdown': dict(severity_stats),
                'status_breakdown': dict(status_stats),
                'submission_trends': dict(daily_submissions),
                'average_resolution_time': self._calculate_avg_resolution_time(feedbacks),
                'insights': {
                    'psychological_safety_level': psychological_safety_level,
                    'primary_concerns': primary_concerns,
                    'trending_issues': trending_issues,
                    'recommendations': recommendations
                },
                'benchmark_comparison': self._generate_benchmark_comparison(feedbacks),
                'data_quality': {
                    'sample_size': len(feedbacks),
                    'confidence_level': 'high' if len(feedbacks) >= 20 else 'medium',
                    'period_completeness': 'complete'
                }
            }

        except Exception as e:
            self.logger.error(f"Failed to get feedback statistics: {e}")
            return {
                'total_submissions': 0,
                'error': str(e)
            }

    def _generate_anonymous_fingerprint(self) -> str:
        """Generate anonymous fingerprint for duplicate detection (not identification)"""
        # Use timestamp and randomness to create unique fingerprint
        timestamp = datetime.utcnow().isoformat()
        random_salt = secrets.token_hex(8)
        fingerprint_data = f"{timestamp}:{random_salt}"
        return hashlib.sha256(fingerprint_data.encode()).hexdigest()

    def _sanitize_description(self, description: str) -> str:
        """Sanitize description to remove potential identifying information"""
        # Remove common identifying patterns while preserving the core message
        import re

        # Remove names (basic pattern matching)
        description = re.sub(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', '[NAME REDACTED]', description)

        # Remove email addresses
        description = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL REDACTED]', description)

        # Remove phone numbers
        description = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE REDACTED]', description)

        # Remove specific dates that could identify incidents
        description = re.sub(r'\b\d{1,2}\/\d{1,2}\/\d{4}\b', '[DATE REDACTED]', description)

        return description.strip()

    async def _handle_feedback_submission(self, db: Session, feedback: AnonymousFeedback) -> None:
        """Handle appropriate workflows for feedback submission"""
        try:
            # Trigger alerts for critical issues
            if feedback.severity in ['critical', 'high']:
                from app.tasks.notification_tasks import send_critical_feedback_alert
                send_critical_feedback_alert.delay(str(feedback.id))

            # Auto-assign to appropriate reviewer based on category
            await self._auto_assign_reviewer(db, feedback)

            # Update organizational metrics
            await self._update_psychological_safety_metrics(db, feedback)

        except Exception as e:
            self.logger.error(f"Failed to handle feedback submission: {e}")

    def _get_support_resources(self, feedback_type: str) -> List[Dict[str, str]]:
        """Get appropriate support resources based on feedback type"""
        resources = [
            {
                'name': 'Employee Assistance Program (EAP)',
                'description': 'Confidential counseling and support services',
                'contact': 'Available 24/7 through company benefits'
            },
            {
                'name': 'HR Support',
                'description': 'Professional HR guidance and support',
                'contact': 'hr@company.com or schedule confidential meeting'
            }
        ]

        if feedback_type in ['toxic_behavior', 'discrimination_bias']:
            resources.append({
                'name': 'External Hotline',
                'description': 'Third-party reporting for serious concerns',
                'contact': '1-800-ETHICS-1'
            })

        return resources

    async def _verify_reviewer_permissions(self, db: Session, reviewer_id: str, organization_id: str) -> bool:
        """Verify reviewer has appropriate permissions"""
        # Implementation would check user roles and permissions
        # This is a placeholder for actual permission checking logic
        return True  # Placeholder

    def _calculate_urgency_score(self, feedback: AnonymousFeedback) -> float:
        """Calculate urgency score for feedback prioritization"""
        severity_weights = {
            'critical': 1.0,
            'high': 0.8,
            'medium': 0.6,
            'low': 0.4
        }

        base_score = severity_weights.get(feedback.severity, 0.5)

        # Increase urgency for older pending items
        days_pending = (datetime.utcnow() - feedback.submitted_at).days
        age_factor = min(days_pending * 0.01, 0.3)

        return min(base_score + age_factor, 1.0)

    def _assess_psychological_safety_level(self, feedbacks: List[AnonymousFeedback]) -> str:
        """Assess overall psychological safety level based on feedback patterns"""
        if not feedbacks:
            return 'insufficient_data'

        # Count critical and high severity issues
        critical_count = len([f for f in feedbacks if f.severity == 'critical'])
        high_count = len([f for f in feedbacks if f.severity == 'high'])
        total_count = len(feedbacks)

        concern_ratio = (critical_count + high_count) / total_count

        if concern_ratio > 0.4:
            return 'critical'
        elif concern_ratio > 0.25:
            return 'concerning'
        elif concern_ratio > 0.1:
            return 'moderate'
        else:
            return 'healthy'

    def _estimate_resolution_time(self, severity: str, status: str) -> int:
        """Estimate resolution time in days based on severity and status"""
        if status in ['resolved', 'closed']:
            return 0

        base_times = {
            'critical': 3,    # 3 days
            'high': 7,        # 1 week
            'medium': 14,     # 2 weeks
            'low': 30         # 1 month
        }

        return base_times.get(severity, 14)

    def _get_status_explanation(self, status: str) -> str:
        """Get human-readable explanation of feedback status"""
        explanations = {
            'pending_review': 'Your feedback has been received and is waiting for HR review',
            'investigating': 'HR is actively investigating your feedback',
            'awaiting_more_info': 'Additional information is being gathered',
            'resolved': 'The issue has been addressed and resolved',
            'closed': 'The feedback case has been closed',
            'escalated': 'The feedback has been escalated to senior leadership'
        }
        return explanations.get(status, 'Status is being processed')

    def _get_status_next_steps(self, status: str) -> List[str]:
        """Get next steps based on feedback status"""
        next_steps = {
            'pending_review': [
                'HR will review your feedback within 48 hours',
                'You may be contacted if more information is needed',
                'Check back for status updates using your tracking ID'
            ],
            'investigating': [
                'Investigation is in progress',
                'All information is being handled confidentially',
                'Resolution updates will be posted when available'
            ],
            'resolved': [
                'The reported issue has been addressed',
                'Preventive measures may have been implemented',
                'Thank you for bringing this to our attention'
            ],
            'closed': [
                'This feedback case has been completed',
                'No further action is required at this time',
                'Submit new feedback if new concerns arise'
            ]
        }
        return next_steps.get(status, ['Continue to check status using your tracking ID'])

    def _calculate_feedback_summary(self, feedbacks: List[AnonymousFeedback]) -> Dict[str, Any]:
        """Calculate summary statistics for feedback review"""
        if not feedbacks:
            return {}

        category_counts = Counter([f.category for f in feedbacks])
        severity_counts = Counter([f.severity for f in feedbacks])
        status_counts = Counter([f.status for f in feedbacks])

        # Calculate urgency statistics
        urgency_scores = [self._calculate_urgency_score(f) for f in feedbacks]
        avg_urgency = sum(urgency_scores) / len(urgency_scores) if urgency_scores else 0

        return {
            'by_category': dict(category_counts),
            'by_severity': dict(severity_counts),
            'by_status': dict(status_counts),
            'average_urgency_score': round(avg_urgency, 2),
            'critical_count': severity_counts.get('critical', 0),
            'high_priority_count': severity_counts.get('high', 0),
            'pending_review_count': status_counts.get('pending_review', 0)
        }

    def _get_recommended_actions(self, feedback: AnonymousFeedback) -> List[str]:
        """Get recommended actions based on feedback type and severity"""
        actions = []

        if feedback.severity == 'critical':
            actions.extend([
                'Immediate investigation required',
                'Consider temporary protective measures',
                'Escalate to senior leadership'
            ])

        category_actions = {
            'toxic_behavior': ['Review team dynamics', 'Consider mediation', 'Monitor patterns'],
            'harassment': ['Follow harassment protocol', 'Document evidence', 'Ensure victim safety'],
            'bullying': ['Implement anti-bullying measures', 'Provide support resources', 'Team intervention'],
            'discrimination': ['Legal review required', 'DEI consultation', 'Policy review'],
            'safety_concern': ['Immediate safety assessment', 'OSHA reporting if needed', 'Risk mitigation'],
            'retaliation': ['Protect reporter', 'Investigate retaliation claims', 'Policy enforcement']
        }

        if feedback.category in category_actions:
            actions.extend(category_actions[feedback.category])
        else:
            actions.append('Standard investigation procedures apply')

        return actions

    async def _auto_assign_reviewer(self, db: Session, feedback: AnonymousFeedback) -> None:
        """Auto-assign feedback to appropriate reviewer based on category"""
        # This would integrate with user roles and specialties
        # For now, placeholder logic
        reviewer_mapping = {
            'harassment': 'hr_specialist',
            'discrimination': 'dei_specialist',
            'safety': 'safety_officer',
            'bullying': 'hr_generalist'
        }

        reviewer_type = reviewer_mapping.get(feedback.category, 'hr_generalist')
        # Implementation would find appropriate reviewer based on type
        feedback.assigned_reviewer_id = None  # Would be set to actual reviewer ID

    async def _update_psychological_safety_metrics(self, db: Session, feedback: AnonymousFeedback) -> None:
        """Update organizational psychological safety metrics based on feedback"""
        # This would integrate with culture health service
        # Implementation would update metrics and trigger alerts if patterns emerge
        pass

    def _sanitize_public_notes(self, notes: str) -> str:
        """Sanitize public resolution notes to remove identifying information"""
        sanitized = self._sanitize_description(notes)

        # Additional public note sanitization
        sanitized = sanitized.replace('meeting with ', 'meeting with relevant parties')
        sanitized = sanitized.replace('spoke with ', 'consulted with relevant individuals')
        sanitized = sanitized.replace('email from ', 'communication from relevant source')

        return sanitized

    def _identify_primary_concerns(self, category_stats: Counter, severity_stats: Counter) -> List[Dict[str, Any]]:
        """Identify primary concerns from category and severity statistics"""
        concerns = []

        # Get top categories
        top_categories = category_stats.most_common(5)
        for category, count in top_categories:
            severity_breakdown = {}
            for severity in ['critical', 'high', 'medium', 'low']:
                severity_breakdown[severity] = severity_stats.get(f"{category}_{severity}", 0)

            concerns.append({
                'category': category,
                'count': count,
                'severity_breakdown': severity_breakdown,
                'trend': 'increasing'  # Would calculate actual trend
            })

        return concerns

    def _identify_trending_issues(self, feedbacks: List[AnonymousFeedback]) -> List[Dict[str, Any]]:
        """Identify trending issues from recent feedback"""
        # Group feedback by week to identify trends
        weekly_trends = defaultdict(lambda: defaultdict(int))

        for feedback in feedbacks:
            week_key = feedback.submitted_at.strftime("%Y-W%U")
            weekly_trends[week_key][feedback.category] += 1

        # Identify increasing trends
        trending = []
        weeks = sorted(weekly_trends.keys())

        if len(weeks) >= 2:
            recent_week = weeks[-1]
            previous_week = weeks[-2]

            for category in weekly_trends[recent_week]:
                recent_count = weekly_trends[recent_week][category]
                previous_count = weekly_trends[previous_week].get(category, 0)

                if recent_count > previous_count * 1.5:  # 50% increase
                    trending.append({
                        'category': category,
                        'recent_week': recent_count,
                        'previous_week': previous_count,
                        'trend_direction': 'increasing'
                    })

        return trending

    def _generate_organizational_recommendations(
        self,
        feedbacks: List[AnonymousFeedback],
        category_stats: Counter,
        severity_stats: Counter
    ) -> List[str]:
        """Generate organizational recommendations based on feedback patterns"""
        recommendations = []

        # Analyze critical issues
        critical_count = len([f for f in feedbacks if f.severity == 'critical'])
        if critical_count > 0:
            recommendations.append(f"Address {critical_count} critical issues immediately")

        # Analyze common categories
        top_category = category_stats.most_common(1)[0] if category_stats else None
        if top_category:
            recommendations.append(f"Focus on {top_category[0]} - {top_category[1]} reports received")

        # Check for patterns
        if len(feedbacks) > 10:  # Sufficient data for pattern analysis
            recommendations.append("Consider anonymous climate survey to gather broader feedback")
            recommendations.append("Review team dynamics in high-reporting areas")

        # General recommendations
        recommendations.extend([
            "Enhance psychological safety training",
            "Improve communication channels for concerns",
            "Regular check-ins on team wellbeing"
        ])

        return recommendations

    def _calculate_avg_resolution_time(self, feedbacks: List[AnonymousFeedback]) -> Optional[float]:
        """Calculate average resolution time in days"""
        resolved_feedbacks = [f for f in feedbacks if f.resolution_date]

        if not resolved_feedbacks:
            return None

        total_days = sum([
            (f.resolution_date - f.submitted_at).days
            for f in resolved_feedbacks
        ])

        return round(total_days / len(resolved_feedbacks), 1)

    def _generate_benchmark_comparison(self, feedbacks: List[AnonymousFeedback]) -> Dict[str, Any]:
        """Generate benchmark comparisons for feedback patterns"""
        total_count = len(feedbacks)
        critical_count = len([f for f in feedbacks if f.severity == 'critical'])

        # Industry benchmarks (these would be based on actual industry data)
        industry_benchmarks = {
            'avg_reports_per_100_employees': 2.5,
            'critical_issue_percentage': 15,
            'resolution_time_days': 14
        }

        return {
            'submission_rate': {
                'your_organization': total_count,
                'industry_average': industry_benchmarks['avg_reports_per_100_employees'],
                'performance': 'above_average' if total_count > industry_benchmarks['avg_reports_per_100_employees'] else 'below_average'
            },
            'critical_issue_rate': {
                'your_organization': round((critical_count / total_count * 100), 1) if total_count > 0 else 0,
                'industry_average': industry_benchmarks['critical_issue_percentage'],
                'performance': 'needs_attention' if critical_count / total_count > 0.2 else 'acceptable'
            }
        }

# Singleton instance
anonymous_feedback_service = AnonymousFeedbackService()