"""
Slack Integration API Endpoints

Why we need these endpoints:
- Receive Slack events (slash commands, interactions)
- Handle OAuth flow for workspace installation
- Manage webhook subscriptions
- Provide Slack app configuration endpoints
"""
from fastapi import APIRouter, Request, BackgroundTasks, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any

from app.core.database import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.integrations.slack.bot import slack_bot
from app.integrations.slack.client import SlackClient
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/events")
async def handle_slack_events(request: Request):
    """
    Handle Slack events and interactions
    
    This endpoint receives:
    - Slash commands (/psychsync, /checkin, /wellness)
    - Interactive components (buttons, modals)
    - Event subscriptions (app mentions, messages)
    
    Slack sends events to this URL which must be configured in:
    Slack App Settings → Event Subscriptions → Request URL
    """
    try:
        # Use Slack Bolt handler to process the request
        return await slack_bot.get_handler().handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack event: {str(e)}")
        return Response(status_code=500)


@router.post("/interactions")
async def handle_slack_interactions(request: Request):
    """
    Handle interactive components
    
    Handles:
    - Button clicks
    - Modal submissions
    - Select menu interactions
    - Message actions
    """
    try:
        return await slack_bot.get_handler().handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack interaction: {str(e)}")
        return Response(status_code=500)


@router.post("/commands")
async def handle_slack_commands(request: Request):
    """
    Handle slash commands
    
    Commands handled:
    - /psychsync [action]
    - /checkin
    - /wellness [team]
    - /assess
    """
    try:
        return await slack_bot.get_handler().handle(request)
    except Exception as e:
        logger.error(f"Error handling Slack command: {str(e)}")
        return Response(status_code=500)


@router.get("/oauth/callback")
async def slack_oauth_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle Slack OAuth callback
    
    Called when:
    - Workspace installs the PsychSync app
    - User authorizes the bot
    
    Process:
    1. Exchange code for access token
    2. Save workspace credentials
    3. Send welcome message
    4. Redirect to success page
    """
    try:
        from slack_sdk.oauth import AuthorizeUrlGenerator
        from slack_sdk.web import WebClient
        
        client = WebClient()
        
        # Exchange code for token
        response = client.oauth_v2_access(
            client_id=settings.SLACK_CLIENT_ID,
            client_secret=settings.SLACK_CLIENT_SECRET,
            code=code
        )
        
        # Extract workspace info
        team_id = response["team"]["id"]
        team_name = response["team"]["name"]
        access_token = response["access_token"]
        bot_user_id = response["bot_user_id"]
        
        # Save to database
        # TODO: Create SlackWorkspace model to store credentials
        logger.info(f"Slack workspace installed: {team_name} ({team_id})")
        
        # Send welcome message
        welcome_client = WebClient(token=access_token)
        welcome_client.chat_postMessage(
            channel=bot_user_id,
            text="🎉 PsychSync installed successfully! Type `/psychsync help` to get started."
        )
        
        return {
            "status": "success",
            "team": team_name,
            "message": "PsychSync installed successfully!"
        }
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}")
        raise HTTPException(status_code=500, detail="OAuth installation failed")


@router.post("/test-connection")
async def test_slack_connection(
    current_user: User = Depends(get_current_user)
):
    """
    Test Slack connection
    
    Admin only - sends test message to verify bot works
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        client = SlackClient()
        
        if not client.is_configured():
            raise HTTPException(status_code=400, detail="Slack not configured")
        
        # Send test message
        response = await client.send_message(
            channel=settings.SLACK_TEST_CHANNEL or "#general",
            text="✅ PsychSync bot is working correctly!",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "✅ *Test Message*\n\nPsychSync Slack integration is configured correctly!"
                    }
                }
            ]
        )
        
        return {
            "status": "success",
            "message": "Test message sent successfully",
            "channel": settings.SLACK_TEST_CHANNEL,
            "ts": response.get("ts") if response else None
        }
        
    except Exception as e:
        logger.error(f"Slack test failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")


@router.post("/send-notification")
async def send_slack_notification(
    channel: str,
    message: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send custom notification to Slack channel
    
    Used by:
    - Admin notifications
    - System alerts
    - Custom integrations
    """
    try:
        client = SlackClient()
        
        # Queue notification to avoid blocking
        background_tasks.add_task(
            client.send_message,
            channel=channel,
            text=message
        )
        
        return {
            "status": "queued",
            "message": "Notification queued for delivery"
        }
        
    except Exception as e:
        logger.error(f"Failed to queue notification: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send notification")


@router.get("/channels")
async def list_slack_channels(
    current_user: User = Depends(get_current_user)
):
    """
    List available Slack channels
    
    Used for:
    - Channel selection in UI
    - Notification routing configuration
    """
    try:
        client = SlackClient()
        
        if not client.is_configured():
            raise HTTPException(status_code=400, detail="Slack not configured")
        
        response = client.client.conversations_list(
            types="public_channel,private_channel",
            exclude_archived=True
        )
        
        channels = [
            {
                "id": ch["id"],
                "name": ch["name"],
                "is_private": ch["is_private"],
                "num_members": ch.get("num_members", 0)
            }
            for ch in response["channels"]
        ]
        
        return {
            "channels": channels,
            "count": len(channels)
        }
        
    except Exception as e:
        logger.error(f"Failed to list channels: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch channels")


@router.get("/status")
async def get_slack_status():
    """
    Get Slack integration status
    
    Returns:
    - Whether Slack is configured
    - Bot connection status
    - Workspace info
    """
    try:
        client = SlackClient()
        
        if not client.is_configured():
            return {
                "status": "not_configured",
                "message": "Slack bot token not configured"
            }
        
        # Test auth
        auth_response = client.client.auth_test()
        
        return {
            "status": "connected",
            "bot_user_id": auth_response.get("user_id"),
            "bot_name": auth_response.get("user"),
            "team_name": auth_response.get("team"),
            "team_id": auth_response.get("team_id")
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/install-url")
async def get_slack_install_url(
    current_user: User = Depends(get_current_user)
):
    """
    Generate Slack installation URL
    
    For distributing app to other workspaces
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    from slack_sdk.oauth import AuthorizeUrlGenerator
    
    generator = AuthorizeUrlGenerator(
        client_id=settings.SLACK_CLIENT_ID,
        scopes=[
            "chat:write",
            "channels:read",
            "groups:read",
            "im:read",
            "im:write",
            "users:read",
            "commands",
            "app_mentions:read"
        ],
        user_scopes=[]
    )
    
    url = generator.generate(state="random_state_string")
    
    return {
        "install_url": url,
        "instructions": "Share this URL to install PsychSync in other workspaces"
    }


@router.delete("/workspace/{team_id}")
async def uninstall_slack_workspace(
    team_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove Slack workspace integration
    
    Called when:
    - Workspace uninstalls app
    - Admin manually removes integration
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # TODO: Delete workspace credentials from database
        logger.info(f"Uninstalling Slack workspace: {team_id}")
        
        return {
            "status": "success",
            "message": f"Workspace {team_id} uninstalled"
        }
        
    except Exception as e:
        logger.error(f"Failed to uninstall workspace: {str(e)}")
        raise HTTPException(status_code=500, detail="Uninstall failed")


# Scheduled jobs (to be called by Celery/cron)
async def send_daily_reminders():
    """
    Send daily assessment reminders via Slack
    
    Called by scheduled job at configured time
    """
    # TODO: Implement scheduled reminder logic
    pass


async def send_team_digest():
    """
    Send daily/weekly team wellness digest
    
    Called by scheduled job
    """
    # TODO: Implement digest logic
    pass