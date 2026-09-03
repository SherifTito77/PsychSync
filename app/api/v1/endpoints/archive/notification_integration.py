"""
Notification Integration API Endpoints
Send notifications to Slack, Teams, and other platforms
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.notification_integration_service import (
    NotificationPriority,
    PlatformType,
    notification_integration_service,
)

router = APIRouter()


# Request schemas
class SendNotificationRequest(BaseModel):
    platform: str  # 'slack' or 'teams'
    message: str
    title: str = ""
    priority: str = "medium"  # 'low', 'medium', 'high', 'critical'
    fields: Optional[Dict[str, str]] = None
    channel: Optional[str] = None  # For Slack


class EmailAlertRequest(BaseModel):
    platform: str
    alert_type: str
    details: Dict[str, Any]


class DailySummaryRequest(BaseModel):
    platform: str
    summary_data: Dict[str, Any]


class TeamDigestRequest(BaseModel):
    platform: str
    team_data: Dict[str, Any]


@router.post("/send")
async def send_notification(
    request: SendNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a custom notification to Slack or Teams

    Args:
        request: Notification details
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        platform = PlatformType(request.platform.lower())
        priority = NotificationPriority(request.priority.lower())

        result = await notification_integration_service.send_notification(
            platform=platform,
            message=request.message,
            title=request.title,
            priority=priority,
            fields=request.fields,
            channel=request.channel,
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Invalid platform or priority: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to send notification: {str(e)}"
        )


@router.post("/email-alert")
async def send_email_alert(
    request: EmailAlertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send an email alert notification (anomaly, stress, critical)

    Args:
        request: Alert details
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        platform = PlatformType(request.platform.lower())

        result = await notification_integration_service.send_email_alert(
            platform=platform, alert_type=request.alert_type, details=request.details
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send alert: {str(e)}")


@router.post("/daily-summary")
async def send_daily_summary(
    request: DailySummaryRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send daily email summary digest

    Args:
        request: Summary data
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        platform = PlatformType(request.platform.lower())

        result = await notification_integration_service.send_daily_summary(
            platform=platform, summary_data=request.summary_data
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send summary: {str(e)}")


@router.post("/team-digest")
async def send_team_digest(
    request: TeamDigestRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send team performance digest

    Args:
        request: Team data
        current_user: Authenticated user
        db: Database session

    Returns:
        Success status
    """
    try:
        platform = PlatformType(request.platform.lower())

        result = await notification_integration_service.send_team_digest(
            platform=platform, team_data=request.team_data
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send digest: {str(e)}")


@router.get("/test")
async def test_notification(
    platform: str = Query(..., description="Platform to test (slack or teams)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send a test notification to verify webhook configuration

    Args:
        platform: Platform to test
        current_user: Authenticated user
        db: Database session

    Returns:
        Test result
    """
    try:
        platform = PlatformType(platform.lower())

        result = await notification_integration_service.send_notification(
            platform=platform,
            message="This is a test notification from PsychSync Email Monitor. Your webhook is configured correctly! 🎉",
            title="✅ Test Notification",
            priority=NotificationPriority.LOW,
        )

        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])

        return {
            **result,
            "message": "Test notification sent successfully! Check your Slack/Teams channel.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid platform: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/configure")
async def configure_webhooks(
    slack_webhook: Optional[str] = None,
    teams_webhook: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Configure webhook URLs for notifications

    Args:
        slack_webhook: Slack webhook URL
        teams_webhook: Teams webhook URL
        current_user: Authenticated user
        db: Database session

    Returns:
        Configuration status
    """
    # TODO: Store webhook URLs in database per user/organization
    # For now, this just validates the URLs

    if not slack_webhook and not teams_webhook:
        raise HTTPException(
            status_code=400, detail="At least one webhook URL must be provided"
        )

    # Validate URLs format
    if slack_webhook and not slack_webhook.startswith("https://hooks.slack.com"):
        raise HTTPException(status_code=400, detail="Invalid Slack webhook URL format")

    if teams_webhook and not teams_webhook.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid Teams webhook URL format")

    return {
        "success": True,
        "message": "Webhook URLs validated (storage not implemented - set via environment variables)",
        "note": "Set SLACK_WEBHOOK_URL and TEAMS_WEBHOOK_URL in your .env file",
    }
