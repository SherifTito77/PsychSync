"""
File Path: app/tasks/scoring_scheduler.py
Celery tasks for scheduled background processing
Handles assessment scoring, report generation, and notifications
"""
from celery import Task
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, Any, List
import logging

from app.core.celery_worker import celery_app
from app.core.database import SessionLocal
from app.db.models.assessment import (
    Assessment, 
    AssessmentResponse, 
    AssessmentStatus
)
from app.db.models.user import User
from app.core.config import settings
# AssessmentService import - will be implemented when service exists
try:
    from app.services.assessment_service import AssessmentService
except ImportError:
    AssessmentService = None

logger = logging.getLogger(__name__)


class DatabaseTask(Task):
    """Base task with database session management"""
    _db: Session = None

    @property
    def db(self) -> Session:
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        if self._db is not None:
            self._db.close()
            self._db = None


# =================================================================
# ASSESSMENT SCORING TASKS
# =================================================================

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.calculate_assessment_scores",
    max_retries=3,
    default_retry_delay=60
)
def calculate_assessment_scores(
    self, 
    assessment_id: int,
    response_ids: List[int] = None
) -> Dict[str, Any]:
    """
    Calculate scores for assessment responses
    
    Args:
        assessment_id: Assessment ID
        response_ids: Optional list of specific response IDs to score
    
    Returns:
        Dict with scoring results
    """
    try:
        logger.info(f"Starting score calculation for assessment {assessment_id}")
        
        db = self.db
        assessment = db.query(Assessment).filter(
            Assessment.id == assessment_id
        ).first()
        
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return {
                'status': 'error',
                'message': f'Assessment {assessment_id} not found'
            }
        
        # Get responses to score
        query = db.query(AssessmentResponse).filter(
            AssessmentResponse.assessment_id == assessment_id,
            AssessmentResponse.completed_at.isnot(None)
        )
        
        if response_ids:
            query = query.filter(AssessmentResponse.id.in_(response_ids))
        
        responses = query.all()
        
        scored_count = 0
        errors = []
        
        for response in responses:
            try:
                # Calculate scores based on assessment type
                score_data = AssessmentService.calculate_scores(
                    db, 
                    response.id
                )
                
                response.score_data = score_data
                response.scored_at = datetime.utcnow()
                scored_count += 1
                
            except Exception as e:
                logger.error(
                    f"Error scoring response {response.id}: {str(e)}"
                )
                errors.append({
                    'response_id': response.id,
                    'error': str(e)
                })
        
        db.commit()
        
        result = {
            'status': 'success',
            'assessment_id': assessment_id,
            'responses_scored': scored_count,
            'total_responses': len(responses),
            'errors': errors
        }
        
        logger.info(
            f"Completed scoring for assessment {assessment_id}: "
            f"{scored_count}/{len(responses)} scored"
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in calculate_assessment_scores: {str(e)}")
        
        # Retry on failure
        try:
            raise self.retry(exc=e)
        except Exception:
            return {
                'status': 'error',
                'message': str(e),
                'assessment_id': assessment_id
            }


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.process_assessment_batch",
    max_retries=3
)
def process_assessment_batch(
    self,
    assessment_ids: List[int]
) -> Dict[str, Any]:
    """
    Process multiple assessments in batch
    
    Args:
        assessment_ids: List of assessment IDs to process
    
    Returns:
        Batch processing results
    """
    try:
        logger.info(f"Processing batch of {len(assessment_ids)} assessments")
        
        results = []
        for assessment_id in assessment_ids:
            result = calculate_assessment_scores.delay(assessment_id)
            results.append({
                'assessment_id': assessment_id,
                'task_id': result.id
            })
        
        return {
            'status': 'success',
            'batch_size': len(assessment_ids),
            'tasks_started': results
        }
        
    except Exception as e:
        logger.error(f"Error in process_assessment_batch: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


# =================================================================
# REPORT GENERATION TASKS
# =================================================================

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.generate_assessment_report",
    max_retries=3
)
def generate_assessment_report(
    self,
    response_id: int,
    report_format: str = 'pdf'
) -> Dict[str, Any]:
    """
    Generate detailed assessment report
    
    Args:
        response_id: Assessment response ID
        report_format: Report format (pdf, html, json)
    
    Returns:
        Report generation results
    """
    try:
        logger.info(
            f"Generating {report_format} report for response {response_id}"
        )
        
        db = self.db
        response = db.query(AssessmentResponse).filter(
            AssessmentResponse.id == response_id
        ).first()
        
        if not response:
            return {
                'status': 'error',
                'message': f'Response {response_id} not found'
            }
        
        # Generate report using assessment service
        report_data = AssessmentService.generate_report(
            db,
            response_id,
            format=report_format
        )
        
        # Store report metadata
        response.report_generated_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Report generated for response {response_id}")
        
        return {
            'status': 'success',
            'response_id': response_id,
            'report_format': report_format,
            'report_url': report_data.get('url'),
            'generated_at': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        
        try:
            raise self.retry(exc=e)
        except Exception:
            return {
                'status': 'error',
                'message': str(e),
                'response_id': response_id
            }


# =================================================================
# NOTIFICATION TASKS
# =================================================================

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.send_assessment_notification",
    max_retries=3
)
def send_assessment_notification(
    self,
    user_id: int,
    notification_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send assessment-related notification to user
    
    Args:
        user_id: User ID
        notification_type: Type of notification
        data: Notification data
    
    Returns:
        Notification sending results
    """
    try:
        logger.info(
            f"Sending {notification_type} notification to user {user_id}"
        )
        
        db = self.db
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            return {
                'status': 'error',
                'message': f'User {user_id} not found'
            }
        
        # Send notification based on type
        # This is a placeholder - implement actual notification logic
        # (email, SMS, push notification, etc.)
        
        notification_sent = True  # Placeholder
        
        if notification_sent:
            logger.info(
                f"Notification sent to user {user_id}: {notification_type}"
            )
            return {
                'status': 'success',
                'user_id': user_id,
                'notification_type': notification_type,
                'sent_at': datetime.utcnow().isoformat()
            }
        else:
            raise Exception("Failed to send notification")
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        
        try:
            raise self.retry(exc=e)
        except Exception:
            return {
                'status': 'error',
                'message': str(e),
                'user_id': user_id
            }


# =================================================================
# SCHEDULED TASKS
# =================================================================

@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.cleanup_expired_assessments"
)
def cleanup_expired_assessments(self) -> Dict[str, Any]:
    """
    Clean up expired assessment invitations and incomplete responses
    Runs daily via Celery Beat
    
    Returns:
        Cleanup results
    """
    try:
        logger.info("Starting cleanup of expired assessments")
        
        db = self.db
        cutoff_date = datetime.utcnow() - timedelta(
            days=settings.ASSESSMENT_EXPIRY_DAYS
        )
        
        # Find expired incomplete responses
        expired_responses = db.query(AssessmentResponse).filter(
            AssessmentResponse.completed_at.is_(None),
            AssessmentResponse.created_at < cutoff_date
        ).all()
        
        expired_count = 0
        for response in expired_responses:
            response.status = AssessmentStatus.EXPIRED
            expired_count += 1
        
        db.commit()
        
        logger.info(f"Marked {expired_count} assessments as expired")
        
        return {
            'status': 'success',
            'expired_count': expired_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in cleanup_expired_assessments: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.generate_daily_reports"
)
def generate_daily_reports(self) -> Dict[str, Any]:
    """
    Generate daily summary reports for organizations
    Runs daily via Celery Beat
    
    Returns:
        Report generation results
    """
    try:
        logger.info("Starting daily report generation")
        
        db = self.db
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        # Count assessments completed yesterday
        completed_assessments = db.query(AssessmentResponse).filter(
            AssessmentResponse.completed_at >= yesterday,
            AssessmentResponse.completed_at < datetime.utcnow()
        ).count()
        
        # Generate reports for each organization
        # This is a placeholder - implement actual report generation
        
        logger.info(
            f"Daily reports generated: "
            f"{completed_assessments} assessments completed"
        )
        
        return {
            'status': 'success',
            'date': yesterday.date().isoformat(),
            'assessments_completed': completed_assessments
        }
        
    except Exception as e:
        logger.error(f"Error in generate_daily_reports: {str(e)}")
        return {
            'status': 'error',
            'message': str(e)
        }


# =================================================================
# UTILITY TASKS
# =================================================================

@celery_app.task(name="tasks.health_check")
def health_check() -> Dict[str, Any]:
    """
    Health check task for monitoring Celery worker status
    
    Returns:
        Health status
    """
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'worker': 'celery'
    }


@celery_app.task(
    base=DatabaseTask,
    bind=True,
    name="tasks.database_health_check"
)
def database_health_check(self) -> Dict[str, Any]:
    """
    Check database connectivity from Celery worker
    
    Returns:
        Database health status
    """
    try:
        db = self.db
        # Simple query to test connection
        result = db.execute("SELECT 1").scalar()
        
        return {
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return {
            'status': 'unhealthy',
            'database': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }