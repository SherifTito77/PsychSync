# app/api/v1/endpoints/email_connections.py
"""
Email Connections API endpoints
OAuth integration and email connection management
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.api.deps import get_current_user, get_db
from app.db.models.user import User
from app.db.models.email_connection import EmailConnection, EmailProvider
# Temporarily disabled due to async conversion issues
# from app.services.email_connector_service import email_connector_service
# from app.services.email_fetching_service import email_fetching_service
# from app.services.email_connection_service import email_connection_service

# Placeholder services
class email_connector_service:
    @staticmethod
    async def get_user_connections(*args, **kwargs):
        return []

class email_fetching_service:
    @staticmethod
    async def test_connection(*args, **kwargs):
        return True

class email_connection_service:
    @staticmethod
    async def disconnect_email(*args, **kwargs):
        return False
from app.core.logging_config import logger

router = APIRouter()


# Pydantic models for request/response
class EmailConnectionRequest(BaseModel):
    provider: EmailProvider
    email_address: EmailStr
    access_token: str
    refresh_token: Optional[str] = None
    account_name: Optional[str] = None
    privacy_settings: Optional[Dict[str, Any]] = None


class EmailConnectionResponse(BaseModel):
    id: str
    provider: EmailProvider
    email_address: str
    account_name: Optional[str]
    is_active: bool
    sync_status: str
    last_sync_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class OAuthUrlResponse(BaseModel):
    authorization_url: str
    state: str


class EmailSyncRequest(BaseModel):
    max_messages: Optional[int] = Field(default=1000, ge=1, le=5000)
    days_back: Optional[int] = Field(default=30, ge=1, le=365)


class EmailSyncResponse(BaseModel):
    success: bool
    messages_processed: int
    sync_status: str
    error_message: Optional[str] = None


@router.post("/connect/oauth-url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    provider: EmailProvider,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get OAuth authorization URL for email provider
    """
    try:
        # Generate state parameter for security
        import secrets
        state = secrets.token_urlsafe(32)

        # Get OAuth URL
        auth_url = await email_connector_service.get_oauth_url(provider, state)

        return OAuthUrlResponse(
            authorization_url=auth_url,
            state=state
        )

    except Exception as e:
        logger.error(f"Error generating OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate OAuth authorization URL"
        )


@router.post("/connect/callback")
async def handle_oauth_callback(
    code: str = Query(...),
    state: str = Query(...),
    provider: EmailProvider = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback from email provider
    """
    try:
        # Exchange authorization code for tokens
        access_token, refresh_token = await email_connector_service.handle_oauth_callback(
            provider, code, state
        )

        # Get user email from token (this would vary by provider)
        # For now, we'll assume the email is provided in a separate step
        # In practice, you'd fetch the user's email from the provider

        # Create email connection
        # Note: In a real implementation, you'd get the email address from the OAuth provider
        # For now, this is a simplified example
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Email address extraction from OAuth token not implemented"
        )

    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete OAuth authentication"
        )


@router.post("/connect/manual", response_model=EmailConnectionResponse)
async def create_manual_connection(
    connection_data: EmailConnectionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create email connection with manually provided OAuth tokens
    """
    try:
        # Validate that this email doesn't already exist for the user
        existing = await email_connection_service.get_connection_by_email_and_provider(
            db, current_user.id, connection_data.email_address, connection_data.provider
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email connection already exists for this address"
            )

        # Create email connection
        email_connection = await email_connector_service.create_email_connection(
            db=db,
            user_id=current_user.id,
            provider=connection_data.provider,
            email_address=connection_data.email_address,
            access_token=connection_data.access_token,
            refresh_token=connection_data.refresh_token,
            account_name=connection_data.account_name,
            privacy_settings=connection_data.privacy_settings
        )

        return EmailConnectionResponse.from_orm(email_connection)

    except Exception as e:
        logger.error(f"Error creating email connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create email connection"
        )


@router.get("/", response_model=List[EmailConnectionResponse])
async def get_email_connections(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all email connections for current user
    """
    try:
        connections = email_connector_service.get_user_connections(db, current_user.id)
        return [EmailConnectionResponse.from_orm(conn) for conn in connections]

    except Exception as e:
        logger.error(f"Error getting email connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email connections"
        )


@router.get("/{connection_id}", response_model=EmailConnectionResponse)
async def get_email_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific email connection
    """
    try:
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email connection not found"
            )

        return EmailConnectionResponse.from_orm(connection)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email connection"
        )


@router.post("/{connection_id}/test", response_model=Dict[str, Any])
async def test_email_connection(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test email connection status
    """
    try:
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email connection not found"
            )

        # Test connection
        is_valid = await email_connector_service.test_connection(db, connection)

        return {
            "connection_id": connection_id,
            "provider": connection.provider.value,
            "email_address": connection.email_address,
            "is_valid": is_valid,
            "last_tested": datetime.utcnow().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing email connection: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test email connection"
        )


@router.post("/{connection_id}/sync", response_model=EmailSyncResponse)
async def sync_emails(
    connection_id: str,
    sync_request: EmailSyncRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Trigger email synchronization for a connection
    """
    try:
        # Verify connection ownership
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email connection not found"
            )

        # Check rate limiting (basic implementation)
        if (connection.last_sync_at and
            (datetime.utcnow() - connection.last_sync_at).total_seconds() < 3600):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Email sync already performed recently. Please wait before syncing again."
            )

        # Update status to syncing
        connection.sync_status = "syncing"
        await db.commit()

        try:
            # Perform sync
            messages_processed = await email_fetching_service.fetch_emails_batch(
                db=db,
                connection=connection,
                max_messages=sync_request.max_messages,
                days_back=sync_request.days_back
            )

            return EmailSyncResponse(
                success=True,
                messages_processed=messages_processed,
                sync_status="completed",
                error_message=None
            )

        except Exception as sync_error:
            # Update connection with error
            connection.sync_status = "error"
            connection.sync_error_message = str(sync_error)
            await db.commit()

            return EmailSyncResponse(
                success=False,
                messages_processed=0,
                sync_status="error",
                error_message=str(sync_error)
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error syncing emails: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to sync emails"
        )


@router.delete("/{connection_id}", response_model=Dict[str, str])
async def disconnect_email(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect and remove email connection
    """
    try:
        success = await email_connector_service.disconnect_email(db, connection_id, current_user.id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email connection not found"
            )

        return {"message": "Email connection successfully disconnected"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error disconnecting email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect email connection"
        )


@router.get("/{connection_id}/stats", response_model=Dict[str, Any])
async def get_email_stats(
    connection_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for email connection
    """
    try:
        # Get connection and stats using service
        connection = await email_connection_service.get_connection_by_id(db, current_user.id, connection_id)

        if not connection or not connection.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email connection not found"
            )

        stats = await email_connection_service.get_connection_stats(db, current_user.id, connection_id)

        return {
            "connection_id": connection_id,
            "provider": connection.provider.value,
            "email_address": connection.email_address,
            "total_emails": stats["total_emails"],
            "recent_emails_30_days": stats["recent_emails"],
            "internal_emails": stats["internal_emails"],
            "external_emails": stats["total_emails"] - stats["internal_emails"],
            "last_sync": connection.last_sync_at.isoformat() if connection.last_sync_at else None,
            "sync_status": connection.sync_status
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting email stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve email statistics"
        )