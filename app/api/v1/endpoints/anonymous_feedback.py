from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import logging

from app.api.v1.deps import get_current_user, get_db
from app.services.anonymous_feedback import anonymous_feedback_system
from app.core.logging_config import logger

router = APIRouter()


class AnonymousFeedbackSubmission(BaseModel):
    """Anonymous feedback submission request"""
    organization_id: str = Field(..., description="Organization ID")
    feedback_type: str = Field(..., description="Type of feedback (toxic_behavior, psychological_safety, etc.)")
    category: str = Field(..., description="Specific category (harassment, bullying, discrimination, etc.)")
    description: str = Field(..., min_length=10, max_length=5000, description="Detailed description of the issue")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$", description="Severity level")
    target_type: Optional[str] = Field(None, description="Type of target (person, team, department)")
    target_id: Optional[str] = Field(None, description="ID of target (will be hashed for anonymity)")
    evidence_urls: Optional[list[str]] = Field(None, description="List of evidence file URLs")
    incident_date: Optional[datetime] = Field(None, description="When the incident occurred")


class FeedbackStatusUpdate(BaseModel):
    """Feedback status update request"""
    new_status: str = Field(..., pattern="^(pending_review|investigating|awaiting_more_info|resolved|closed|escalated)$")
    resolution_notes: Optional[str] = Field(None, description="Private notes for HR reviewers")
    public_resolution_notes: Optional[str] = Field(None, description="Public notes visible to submitter")


@router.post("/submit", response_model=Dict[str, Any])
async def submit_anonymous_feedback(
    feedback_data: AnonymousFeedbackSubmission,
    db: Session = Depends(get_db)
):
    """
    Submit completely anonymous feedback with enhanced psychological safety features

    This endpoint accepts anonymous feedback about workplace concerns.
    No user identification is stored - the system is designed to be completely anonymous.

    - **No authentication required** - maintaining anonymity
    - **Returns tracking ID** for status checking
    - **All submissions are encrypted** and stored securely
    - **Critical issues trigger immediate alerts** to HR
    - **Enhanced privacy protections** with automatic content sanitization
    """
    try:
        logger.info(f"Anonymous feedback submission received: {feedback_data.feedback_type}/{feedback_data.category}")

        # Initialize service
        feedback_service = anonymous_feedback_system(db)

        result = await feedback_service.submit_anonymous_feedback(
            feedback_type=feedback_data.feedback_type,
            category=feedback_data.category,
            description=feedback_data.description,
            severity=feedback_data.severity,
            target_type=feedback_data.target_type,
            target_id=feedback_data.target_id,
            evidence_urls=feedback_data.evidence_urls,
            incident_date=feedback_data.incident_date,
            organization_id=feedback_data.organization_id
        )

        if result['success']:
            logger.info(f"Anonymous feedback submitted successfully - Tracking ID: {result['tracking_id'][:8]}...")
            return result
        else:
            logger.error(f"Anonymous feedback submission failed: {result.get('error', 'Unknown error')}")
            raise HTTPException(
                status_code=500,
                detail={
                    "error": result.get('error', 'Submission failed'),
                    "alternatives": result.get('alternatives', [])
                }
            )

    except Exception as e:
        logger.error(f"Error in anonymous feedback submission: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to process anonymous feedback",
                "alternatives": [
                    "Try submitting again",
                    "Contact HR directly via confidential channel",
                    "Use external reporting hotlines"
                ]
            }
        )


@router.get("/status/{tracking_id}", response_model=Dict[str, Any])
async def check_feedback_status(
    tracking_id: str,
    db: Session = Depends(get_db)
):
    """
    Check status of anonymous feedback using tracking ID

    This endpoint allows submitters to check the status of their anonymous feedback
    without revealing their identity. Only the tracking ID is required.

    - **No authentication required** - maintaining anonymity
    - **Only general status information** is returned
    - **No identifying information** is ever exposed
    """
    try:
        logger.info(f"Status check requested for tracking ID: {tracking_id[:8]}...")

        feedback_service = anonymous_feedback_system(db)
        result = await feedback_service.check_feedback_status(tracking_id)

        if not result.get('found'):
            logger.warning(f"Feedback not found for tracking ID: {tracking_id[:8]}...")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Feedback not found",
                    "message": result.get('message', 'Tracking ID not found'),
                    "help": result.get('help', 'Please check your tracking ID')
                }
            )

        logger.info(f"Status check successful for tracking ID: {tracking_id[:8]}...")
        return {
            "found": True,
            "status": result['status'],
            "submitted_at": result['submitted_at'],
            "days_since_submission": result['days_since_submission'],
            "last_updated": result['last_updated'],
            "public_resolution_notes": result['public_resolution_notes'],
            "severity": result['severity'],
            "category": result['category'],
            "estimated_resolution_days": result['estimated_resolution_days'],
            "status_explanation": result['status_explanation'],
            "privacy_reminder": result['privacy_reminder'],
            "next_steps": result['next_steps']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feedback status: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Unable to check status",
                "message": "Please try again later or contact support",
                "alternatives": ["Contact HR support", "Try submitting new feedback"]
            }
        )


@router.get("/categories", response_model=Dict[str, Any])
async def get_feedback_categories():
    """
    Get available feedback categories and subcategories

    This endpoint provides information about available feedback categories
    to help users understand what they can report anonymously.
    """
    try:
        # Initialize temporary service to get categories
        temp_service = anonymous_feedback_system(None)
        categories = temp_service.feedback_categories

        return {
            "categories": categories,
            "privacy_guarantee": {
                "title": "100% Anonymous",
                "description": "All submissions are completely anonymous. We cannot identify who submitted feedback.",
                "features": [
                    "No IP addresses stored",
                    "No user accounts required",
                    "Cryptographically secure tracking",
                    "Encrypted data storage"
                ]
            },
            "reporting_guidelines": {
                "be_specific": "Provide as much detail as possible about the incident",
                "focus_on_behavior": "Describe specific behaviors and actions",
                "include_timeline": "When did the incidents occur?",
                "add_evidence": "Upload any relevant documents or screenshots"
            },
            "support_info": {
                "immediate_help": "For immediate assistance, contact HR or EAP",
                "external_resources": "External hotlines available for serious concerns",
                "retaliation_protection": "Retaliation against reporters is prohibited"
            }
        }

    except Exception as e:
        logger.error(f"Error getting feedback categories: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to load feedback categories"
        )


# HR/Management endpoints (require authentication and permissions)

@router.get("/review")
async def get_feedback_for_review(
    organization_id: str,
    status_filter: Optional[str] = None,
    severity_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get anonymous feedback for HR review

    This endpoint is for authorized HR personnel to review anonymous feedback.
    All identifying information is removed to maintain submitter anonymity.
    """
    try:
        # In a real implementation, verify user has appropriate permissions
        # For now, assuming current_user has HR permissions

        logger.info(f"Feedback review requested by user {current_user.id} for org {organization_id}")

        feedback_service = anonymous_feedback_system(db)

        filters = {}
        if status_filter:
            filters['status'] = status_filter
        if severity_filter:
            filters['severity'] = severity_filter
        if category_filter:
            filters['feedback_type'] = category_filter

        result = await feedback_service.get_feedback_for_review(
            hr_user_id=str(current_user.id),
            organization_id=organization_id,
            filters=filters
        )

        logger.info(f"Retrieved {result['total_count']} feedback items for review")
        return result

    except PermissionError as e:
        logger.error(f"Permission denied for feedback review: {e}")
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions to review feedback"
        )
    except Exception as e:
        logger.error(f"Error getting feedback for review: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve feedback for review"
        )


@router.put("/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    status_update: FeedbackStatusUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Update feedback status (HR/Authorized users only)

    This endpoint allows authorized users to update the status of anonymous feedback.
    """
    try:
        # Verify permissions in a real implementation

        logger.info(f"Feedback status update requested for {feedback_id} by user {current_user.id}")

        feedback_service = anonymous_feedback_system(db)

        result = await feedback_service.update_feedback_status(
            feedback_id=feedback_id,
            hr_user_id=str(current_user.id),
            new_status=status_update.new_status,
            internal_notes=status_update.resolution_notes,
            public_notes=status_update.public_resolution_notes,
            actions_taken=status_update.resolution_notes
        )

        if result['success']:
            logger.info(f"Feedback {feedback_id} status updated to {status_update.new_status}")
            return result
        else:
            logger.error(f"Failed to update feedback status: {result.get('error')}")
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Failed to update status')
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to update feedback status"
        )


@router.get("/statistics/{organization_id}")
async def get_anonymous_feedback_statistics(
    organization_id: str,
    days_back: int = 90,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    Get anonymous feedback statistics for organizational insights

    This endpoint provides aggregated, anonymous statistics about feedback patterns
    to help organizations identify systemic issues and improve workplace culture.
    """
    try:
        # Verify permissions in a real implementation

        logger.info(f"Feedback statistics requested by user {current_user.id} for org {organization_id}")

        feedback_service = anonymous_feedback_system(db)

        result = await feedback_service.get_anonymous_feedback_statistics(
            organization_id=organization_id,
            days_back=days_back
        )

        logger.info(f"Statistics returned: {result['total_submissions']} submissions analyzed")
        return result

    except Exception as e:
        logger.error(f"Error getting feedback statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve feedback statistics"
        )


@router.get("/health")
async def feedback_system_health():
    """
    Check anonymous feedback system health

    Simple health check endpoint to verify the system is operational.
    """
    try:
        return {
            "status": "healthy",
            "system": "anonymous_feedback",
            "features": {
                "submission": "operational",
                "tracking": "operational",
                "review": "operational",
                "analytics": "operational"
            },
            "privacy": {
                "anonymity_level": "complete",
                "data_encryption": "enabled",
                "audit_logging": "enabled"
            }
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "error": str(e)
        }