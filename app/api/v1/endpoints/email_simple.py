# app/api/v1/endpoints/email_simple.py
"""
Simplified Email Connection Endpoint (No OAuth)
Easy setup for non-technical users using IMAP and app passwords
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, validator

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.db.models.email_connection import EmailConnection
from app.services.free_email_connector_service import free_email_connector_service
from app.services.email_fetching_service import email_fetching_service
from app.services.email_connection_service import email_connection_service
from app.core.logging_config import logger

router = APIRouter()

# IMAP Server Configurations for Popular Providers
IMAP_PROVIDERS = {
    'gmail': {
        'host': 'imap.gmail.com',
        'port': 993,
        'use_ssl': True,
        'name': 'Gmail',
        'app_password_help': 'Use Google App Password: https://myaccount.google.com/apppasswords'
    },
    'outlook': {
        'host': 'outlook.office365.com',
        'port': 993,
        'use_ssl': True,
        'name': 'Outlook/Hotmail',
        'app_password_help': 'Use Microsoft App Password: https://account.live.com/developers/applications'
    },
    'yahoo': {
        'host': 'imap.mail.yahoo.com',
        'port': 993,
        'use_ssl': True,
        'name': 'Yahoo Mail',
        'app_password_help': 'Use Yahoo App Password: https://login.yahoo.com/account/security/app-passwords'
    },
    'icloud': {
        'host': 'imap.mail.me.com',
        'port': 993,
        'use_ssl': True,
        'name': 'iCloud Mail',
        'app_password_help': 'Use app-specific password from iCloud settings'
    },
    'aol': {
        'host': 'imap.aol.com',
        'port': 993,
        'use_ssl': True,
        'name': 'AOL Mail',
        'app_password_help': 'Use AOL App Password'
    }
}

class SimpleEmailConnection(BaseModel):
    """Simple email connection model - no OAuth complexity"""
    email_address: EmailStr = Field(..., description="Email address to connect")
    app_password: str = Field(..., min_length=1, description="App password (not regular password)")
    provider: str = Field(..., description="Email provider")
    display_name: Optional[str] = Field(None, description="Display name for this email account")

    @validator('provider')
    def validate_provider(cls, v):
        if v not in IMAP_PROVIDERS:
            raise ValueError(f'Provider must be one of: {", ".join(IMAP_PROVIDERS.keys())}')
    return v

class EmailSetupGuide(BaseModel):
    """Email setup guide for different providers"""
    provider: str
    setup_steps: List[str]
    app_password_url: str
    common_issues: List[str]
    estimated_time: str

class QuickTest(BaseModel):
    """Quick test of email connection"""
    provider: str
    email_address: str
    app_password: str

class SyncOptions(BaseModel):
    """Email sync options"""
    days_back: int = Field(30, ge=1, le=365, description="Number of days of emails to analyze")
    max_emails: int = Field(1000, ge=100, le=10000, description="Maximum emails to fetch")
    include_sent: bool = Field(True, description="Include sent emails in analysis")
    analyze_contacts: bool = Field(True, description="Analyze communication patterns")

@router.get("/providers", response_model=Dict[str, Any])
async def get_email_providers():
    """Get list of supported email providers with setup information"""
    return {
        "providers": IMAP_PROVIDERS,
        "default_provider": "gmail",
        "setup_guide_url": "/api/v1/email-simple/setup-guide",
        "most_popular": ["gmail", "outlook", "yahoo"]
    }

@router.get("/setup-guide/{provider}", response_model=EmailSetupGuide)
async def get_setup_guide(provider: str):
    """Get setup guide for specific email provider"""

    if provider not in IMAP_PROVIDERS:
        raise HTTPException(
            status_code=404,
            detail=f"Provider {provider} not supported"
        )

    provider_info = IMAP_PROVIDERS[provider]

    # Generate setup steps based on provider
    setup_steps = []
    common_issues = []

    if provider == 'gmail':
        setup_steps = [
            "Go to your Google Account settings",
            "Click on 'Security'",
            "Enable 2-Step Verification (required)",
            "Go to 'App passwords'",
            "Select 'Mail' app",
            "Generate 16-character app password",
            "Copy the app password (not your regular password!)"
        ]
        app_password_url = "https://myaccount.google.com/apppasswords"
        common_issues = [
            "2-Step Verification must be enabled first",
            "Use the app password, not your regular password",
            "Don't include spaces in the app password",
            "Make sure to select 'Mail' as the app type"
        ]
        estimated_time = "2-3 minutes"

    elif provider == 'outlook':
        setup_steps = [
            "Go to Microsoft account security page",
            "Click on 'Advanced security options'",
            "Add a new app password",
            "Create a name for your app",
            "Copy the generated app password"
        ]
        app_password_url = "https://account.live.com/developers/applications"
        common_issues = [
            "App passwords may take a few minutes to activate",
            "Make sure to use the full password including special characters",
            "Some corporate accounts may not allow app passwords"
        ]
        estimated_time = "3-5 minutes"

    elif provider == 'yahoo':
        setup_steps = [
            "Go to Yahoo Account Security",
            "Click on 'Account security'",
            "Go to 'App passwords'",
            "Select 'Mail app'",
            "Generate app password",
            "Copy the app password"
        ]
        app_password_url = "https://login.yahoo.com/account/security/app-passwords"
        common_issues = [
            "Must have 2FA enabled for app passwords",
            "App passwords expire after 1 year",
            "Use the app password immediately after generating"
        ]
        estimated_time = "2-3 minutes"

    else:  # Default setup for other providers
        setup_steps = [
            f"Enable 2-factor authentication for {provider_info['name']}",
            f"Find app password settings in {provider_info['name']} account",
            "Generate a new app password for this application",
            "Copy the app password",
            "Test the connection"
        ]
        app_password_url = f"https://{provider_info['name']}.com/security"
        common_issues = [
            "Check if your provider supports app passwords",
            "Corporate accounts may require administrator approval",
            "Try different server settings if connection fails"
        ]
        estimated_time = "5-10 minutes"

    return EmailSetupGuide(
        provider=provider,
        setup_steps=setup_steps,
        app_password_url=app_password_url,
        common_issues=common_issues,
        estimated_time=estimated_time
    )

@router.post("/quick-test", response_model=Dict[str, Any])
async def quick_test_connection(test_data: QuickTest):
    """Quick test of email connection without saving"""

    try:
        # Test connection
        is_valid, message = free_email_connector_service.test_imap_connection(
            test_data.email_address,
            test_data.app_password
        )

        # Get server info
        server_info = IMAP_PROVIDERS.get(test_data.provider, {})

        return {
            "success": is_valid,
            "message": message,
            "provider": test_data.provider,
            "server_info": server_info,
            "next_steps": "Save connection if test successful"
        }

    except Exception as e:
        logger.error(f"Quick email connection test failed: {e}")
        return {
            "success": False,
            "message": f"Connection test failed: {str(e)}",
            "error": str(e),
            "suggestion": "Check your email and app password, then try again"
        }

@router.post("/connect", response_model=Dict[str, Any])
async def connect_email_simple(
    connection_data: SimpleEmailConnection,
    sync_options: SyncOptions = SyncOptions(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Connect email account using simple IMAP connection (no OAuth)
    Perfect for non-technical users
    """

    try:
        logger.info(f"User {current_user.id} connecting email {connection_data.email_address}")

        # Validate that this email doesn't already exist for the user
        existing = await email_connection_service.get_connection_by_email(
            db, current_user.id, connection_data.email_address
        )

        if existing:
            return {
                "success": False,
                "error": "Email already connected",
                "message": "This email address is already connected to your account",
                "existing_connection_id": str(existing.id)
            }

        # Test connection first
        is_valid, test_message = free_email_connector_service.test_imap_connection(
            connection_data.email_address,
            connection_data.app_password
        )

        if not is_valid:
            return {
                "success": False,
                "error": "Connection test failed",
                "message": test_message,
                "suggestion": "Check your app password and try again",
                "help_url": f"/api/v1/email-simple/setup-guide/{connection_data.provider}"
            }

        # Create email connection
        email_connection = await free_email_connector_service.create_free_connection(
            db=db,
            user_id=current_user.id,
            email_address=connection_data.email_address,
            app_password=connection_data.app_password,
            account_name=connection_data.display_name or connection_data.email_address.split('@')[0],
            custom_imap_config={
                "host": IMAP_PROVIDERS[connection_data.provider]["host"],
                "port": IMAP_PROVIDERS[connection_data.provider]["port"],
                "use_ssl": IMAP_PROVIDERS[connection_data.provider]["use_ssl"],
                "use_starttls": IMAP_PROVIDERS[connection_data.provider].get("use_starttls", False)
            }
        )

        # Initial email sync
        try:
            messages_processed = await email_fetching_service.fetch_emails_batch(
                db=db,
                connection=email_connection,
                max_messages=sync_options.max_emails,
                days_back=sync_options.days_back
            )

            sync_status = "completed" if messages_processed > 0 else "no_messages"

        except Exception as sync_error:
            logger.warning(f"Initial sync failed for {connection_data.email_address}: {sync_error}")
            messages_processed = 0
            sync_status = "sync_failed"

        # Log successful connection
        logger.info(f"Successfully connected email {connection_data.email_address} for user {current_user.id}")

        return {
            "success": True,
            "connection_id": str(email_connection.id),
            "email_address": connection_data.email_address,
            "provider": connection_data.provider,
            "display_name": connection_data.display_name,
            "messages_processed": messages_processed,
            "sync_status": sync_status,
            "message": "Email connection successful!",
            "next_steps": [
                "Wait for initial analysis to complete",
                "Check your behavioral insights dashboard",
                "Connect additional email accounts for comprehensive analysis"
            ],
            "test_result": test_message
        }

    except Exception as e:
        logger.error(f"Email connection failed for user {current_user.id}: {e}")
        return {
            "success": False,
            "error": "Connection failed",
            "message": str(e),
            "suggestion": "Please check your credentials and try again"
        }

@router.get("/my-connections", response_model=List[Dict[str, Any]])
async def get_my_connections(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's email connections"""

    try:
        # Get connections with stats using service
        connections_with_stats = await email_connection_service.get_connections_with_stats(
            db, current_user.id
        )

        connection_list = []
        for item in connections_with_stats:
            conn = item["connection"]
            stats = item["stats"]

            connection_list.append({
                "id": str(conn.id),
                "email_address": conn.email_address,
                "provider": conn.provider,
                "display_name": conn.account_name,
                "created_at": conn.created_at.isoformat(),
                "last_sync": conn.last_sync_at.isoformat() if conn.last_sync_at else None,
                "sync_status": conn.sync_status,
                "total_emails": stats["total_emails"],
                "recent_emails_30_days": stats["recent_emails"],
                "internal_emails": stats["internal_emails"],
                "is_active": conn.is_active
            })

        return connection_list

    except Exception as e:
        logger.error(f"Failed to get connections for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve email connections"
        )

@router.post("/{connection_id}/sync", response_model=Dict[str, Any])
async def sync_emails_simple(
    connection_id: str,
    sync_options: SyncOptions = SyncOptions(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Sync emails for a specific connection"""

    try:
        # Verify connection ownership using service
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=404,
                detail="Email connection not found"
            )

        # Check rate limiting (basic implementation)
        if (connection.last_sync_at and
            (datetime.utcnow() - connection.last_sync_at).total_seconds() < 1800):  # 30 minutes
            raise HTTPException(
                status_code=429,
                detail="Email sync too recent. Please wait 30 minutes between syncs."
            )

        # Update status
        connection.sync_status = "syncing"
        await db.commit()

        # Perform sync
        try:
            messages_processed = await email_fetching_service.fetch_emails_batch(
                db=db,
                connection=connection,
                max_messages=sync_options.max_emails,
                days_back=sync_options.days_back
            )

            # Update connection
            connection.last_sync_at = datetime.utcnow()
            connection.sync_status = "completed"
            await db.commit()

            return {
                "success": True,
                "messages_processed": messages_processed,
                "sync_status": "completed",
                "connection_id": connection_id,
                "sync_options": {
                    "days_back": sync_options.days_back,
                    "max_emails": sync_options.max_emails
                },
                "message": f"Successfully synced {messages_processed} emails"
            }

        except Exception as sync_error:
            # Update connection with error
            connection.sync_status = "error"
            connection.sync_error_message = str(sync_error)
            await db.commit()

            return {
                "success": False,
                "messages_processed": 0,
                "sync_status": "error",
                "error": str(sync_error),
                "suggestion": "Please try again later or check your email settings"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email sync failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to sync emails"
        )

@router.delete("/{connection_id}", response_model=Dict[str, str])
async def delete_connection_simple(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete email connection"""

    try:
        # Verify connection ownership using service
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=404,
                detail="Email connection not found"
            )

        # Soft delete (keep data but deactivate)
        connection.is_active = False
        connection.deactivated_at = datetime.utcnow()
        connection.deactivated_by = current_user.id
        await db.commit()

        logger.info(f"User {current_user.id} deactivated email connection {connection_id}")

        return {
            "message": "Email connection successfully deactivated",
            "connection_id": connection_id,
            "data_retained": "Your email analysis data is preserved but no new emails will be synced"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete email connection: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete email connection"
        )

@router.get("/connection-status/{connection_id}", response_model=Dict[str, Any])
async def get_connection_status(
    connection_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed status of email connection"""

    try:
        # Verify connection ownership
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection:
            raise HTTPException(
                status_code=404,
                detail="Email connection not found"
            )

        # Get email statistics using service
        stats = await email_connection_service.get_connection_stats(db, current_user.id, connection_id)

        # Get recent sync status
        last_sync = connection.last_sync_at
        days_since_sync = None
        if last_sync:
            days_since_sync = (datetime.utcnow() - last_sync).days

        return {
            "connection_id": connection_id,
            "email_address": connection.email_address,
            "provider": connection.provider,
            "is_active": connection.is_active,
            "sync_status": connection.sync_status,
            "created_at": connection.created_at.isoformat(),
            "last_sync": last_sync.isoformat() if last_sync else None,
            "days_since_sync": days_since_sync,
            "total_emails_analyzed": stats["total_emails"],
            "emails_last_30_days": stats["recent_emails"],
            "server_info": IMAP_PROVIDERS.get(connection.provider, {}),
            "needs_attention": (
                not connection.is_active or
                (days_since_sync and days_since_sync > 7) or
                connection.sync_status == "error"
            )
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get connection status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve connection status"
        )

@router.get("/help/troubleshooting", response_model=Dict[str, Any])
async def get_troubleshooting_help():
    """Get troubleshooting help for email connection issues"""

    return {
        "common_issues": {
            "app_password_not_working": {
                "problem": "App password not working",
                "solution": [
                    "Make sure 2-factor authentication is enabled",
                    "Generate a new app password",
                    "Use the app password, not your regular password",
                    "Don't include spaces in the password"
                ],
                "related_providers": ["gmail", "outlook", "yahoo"]
            },
            "connection_timeout": {
                "problem": "Connection times out",
                "solution": [
                    "Check your internet connection",
                    "Verify server settings are correct",
                    "Try connecting to a different network",
                    "Firewall may be blocking IMAP port 993"
                ],
                "all_providers": True
            },
            "authentication_failed": {
                "problem": "Authentication failed",
                "solution": [
                    "Double-check email address spelling",
                    "Regenerate the app password",
                    "Make sure app password doesn't expire",
                    "Check if account is locked or suspended"
                ],
                "all_providers": True
            },
            "no_emails_found": {
                "problem": "No emails found during sync",
                "solution": [
                    "Check if email account has emails",
                    "Verify IMAP is enabled in email settings",
                    "Try adjusting sync date range",
                    "Check email filters that might hide emails"
                ],
                "all_providers": True
            }
        },
        "emergency_help": {
            "contact_support": "Contact our support team",
            "email": "support@psychsync.ai",
            "documentation": "Check our setup guides",
            "community": "Ask in our community forum"
        },
        "success_indicators": {
            "connection_working": "Connection test succeeds",
            "sync_successful": "Emails are being processed",
            "analysis_complete": "Behavioral insights appear in dashboard"
        }
    }