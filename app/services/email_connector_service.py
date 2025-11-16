# app/services/email_connector_service.py
"""
Email Connector Service - Handles OAuth authentication and email fetching
Supports Gmail, Outlook, Office365, Exchange, and IMAP connections
"""

import json
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import imaplib
import email
from email.header import decode_header
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import requests
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.models.email_connection import EmailConnection, EmailProvider
from app.db.models.email_metadata import EmailMetadata
from app.core.logging_config import logger


class EmailConnectorService:
    """Service for managing email connections and fetching email metadata"""

    def __init__(self):
        # Initialize encryption key for token storage
        self.encryption_key = self._get_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # OAuth configurations
        self.gmail_config = {
            "client_id": settings.GMAIL_CLIENT_ID,
            "client_secret": settings.GMAIL_CLIENT_SECRET,
            "redirect_uri": settings.EMAIL_CALLBACK_URL,
            "scopes": [
                "https://www.googleapis.com/auth/gmail.readonly",
                "https://www.googleapis.com/auth/userinfo.email"
            ]
        }

        self.outlook_config = {
            "client_id": settings.OUTLOOK_CLIENT_ID,
            "client_secret": settings.OUTLOOK_CLIENT_SECRET,
            "redirect_uri": settings.EMAIL_CALLBACK_URL,
            "scopes": [
                "https://graph.microsoft.com/Mail.Read",
                "https://graph.microsoft.com/User.Read"
            ],
            "authority": "https://login.microsoftonline.com"
        }

    def _get_encryption_key(self) -> bytes:
        """Generate or retrieve encryption key for token storage"""
        key_material = settings.ENCRYPTION_KEY.encode() if hasattr(settings, 'ENCRYPTION_KEY') else b'default-key-material-for-psychsync-email-encryption'
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b'psychsync_email_salt',
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(key_material))

    def encrypt_token(self, token_data: str) -> str:
        """Encrypt OAuth token data for secure storage"""
        return self.cipher_suite.encrypt(token_data.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt OAuth token data"""
        return self.cipher_suite.decrypt(encrypted_token.encode()).decode()

    async def get_oauth_url(self, provider: EmailProvider, state: str) -> str:
        """Generate OAuth authorization URL for email provider"""
        if provider == EmailProvider.GMAIL:
            return self._get_gmail_oauth_url(state)
        elif provider in [EmailProvider.OUTLOOK, EmailProvider.OFFICE365]:
            return self._get_outlook_oauth_url(state)
        else:
            raise ValueError(f"OAuth not supported for provider: {provider}")

    def _get_gmail_oauth_url(self, state: str) -> str:
        """Generate Gmail OAuth URL"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.gmail_config["client_id"],
                    "client_secret": self.gmail_config["client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.gmail_config["scopes"],
            redirect_uri=self.gmail_config["redirect_uri"]
        )

        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=state,
            prompt='consent'
        )
        return auth_url

    def _get_outlook_oauth_url(self, state: str) -> str:
        """Generate Outlook OAuth URL"""
        base_url = "https://login.microsoftonline.com/common/oauth2/v2.0/authorize"
        params = {
            "client_id": self.outlook_config["client_id"],
            "response_type": "code",
            "redirect_uri": self.outlook_config["redirect_uri"],
            "scope": " ".join(self.outlook_config["scopes"]),
            "state": state,
            "response_mode": "query"
        }

        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{param_string}"

    async def handle_oauth_callback(self, provider: EmailProvider, code: str, state: str) -> Tuple[str, str]:
        """Handle OAuth callback and return access and refresh tokens"""
        if provider == EmailProvider.GMAIL:
            return await self._handle_gmail_callback(code)
        elif provider in [EmailProvider.OUTLOOK, EmailProvider.OFFICE365]:
            return await self._handle_outlook_callback(code)
        else:
            raise ValueError(f"OAuth callback not supported for provider: {provider}")

    async def _handle_gmail_callback(self, code: str) -> Tuple[str, str]:
        """Handle Gmail OAuth callback"""
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": self.gmail_config["client_id"],
                    "client_secret": self.gmail_config["client_secret"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=self.gmail_config["scopes"],
            redirect_uri=self.gmail_config["redirect_uri"]
        )

        flow.fetch_token(code=code)
        credentials = flow.credentials

        access_token = credentials.token
        refresh_token = credentials.refresh_token

        if not refresh_token:
            logger.warning("No refresh token received from Gmail")

        return access_token, refresh_token

    async def _handle_outlook_callback(self, code: str) -> Tuple[str, str]:
        """Handle Outlook OAuth callback"""
        token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
        data = {
            "client_id": self.outlook_config["client_id"],
            "client_secret": self.outlook_config["client_secret"],
            "code": code,
            "redirect_uri": self.outlook_config["redirect_uri"],
            "grant_type": "authorization_code",
            "scope": " ".join(self.outlook_config["scopes"])
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()
        token_data = response.json()

        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")

        return access_token, refresh_token

    async def create_email_connection(
        self,
        db: Session,
        user_id: str,
        provider: EmailProvider,
        email_address: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_name: Optional[str] = None,
        privacy_settings: Optional[Dict] = None
    ) -> EmailConnection:
        """Create new email connection with encrypted credentials"""

        # Encrypt tokens
        encrypted_access_token = self.encrypt_token(access_token)
        encrypted_refresh_token = self.encrypt_token(refresh_token) if refresh_token else None

        # Calculate token expiration (Gmail tokens expire in 1 hour)
        token_expires_at = datetime.utcnow() + timedelta(hours=1)

        email_connection = EmailConnection(
            user_id=user_id,
            provider=provider,
            email_address=email_address,
            account_name=account_name or email_address,
            access_token_encrypted=encrypted_access_token,
            refresh_token_encrypted=encrypted_refresh_token,
            token_expires_at=token_expires_at,
            is_active=True,
            sync_status="pending",
            privacy_settings=privacy_settings or {
                "analyze_internal_only": True,
                "exclude_sensitive_subjects": True,
                "min_message_age_days": 30,
                "max_messages_per_batch": 1000
            }
        )

        db.add(email_connection)
        await db.commit()
        await db.refresh(email_connection)

        logger.info(f"Created email connection for user {user_id}, provider {provider}")
        return email_connection

    async def refresh_access_token(self, db: Session, connection: EmailConnection) -> bool:
        """Refresh access token for email connection"""
        if not connection.refresh_token_encrypted:
            logger.error(f"No refresh token available for connection {connection.id}")
            return False

        try:
            refresh_token = self.decrypt_token(connection.refresh_token_encrypted)

            if connection.provider == EmailProvider.GMAIL:
                credentials = Credentials(
                    token=connection.access_token_encrypted,
                    refresh_token=refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=self.gmail_config["client_id"],
                    client_secret=self.gmail_config["client_secret"]
                )

                credentials.refresh(Request())

                # Update encrypted tokens
                connection.access_token_encrypted = self.encrypt_token(credentials.token)
                connection.token_expires_at = credentials.expiry

            elif connection.provider in [EmailProvider.OUTLOOK, EmailProvider.OFFICE365]:
                token_url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
                data = {
                    "client_id": self.outlook_config["client_id"],
                    "client_secret": self.outlook_config["client_secret"],
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": " ".join(self.outlook_config["scopes"])
                }

                response = requests.post(token_url, data=data)
                response.raise_for_status()
                token_data = response.json()

                new_access_token = token_data.get("access_token")
                new_refresh_token = token_data.get("refresh_token", refresh_token)

                connection.access_token_encrypted = self.encrypt_token(new_access_token)
                connection.refresh_token_encrypted = self.encrypt_token(new_refresh_token)
                connection.token_expires_at = datetime.utcnow() + timedelta(hours=1)

            await db.commit()
            logger.info(f"Successfully refreshed token for connection {connection.id}")
            return True

        except Exception as e:
            logger.error(f"Failed to refresh token for connection {connection.id}: {e}")
            connection.sync_status = "error"
            connection.sync_error_message = f"Token refresh failed: {str(e)}"
            await db.commit()
            return False

    async def test_connection(self, db: Session, connection: EmailConnection) -> bool:
        """Test if email connection is working"""
        try:
            # Check if token needs refresh
            if connection.token_expires_at and connection.token_expires_at <= datetime.utcnow():
                if not await self.refresh_access_token(db, connection):
                    return False

            if connection.provider == EmailProvider.GMAIL:
                return await self._test_gmail_connection(connection)
            elif connection.provider in [EmailProvider.OUTLOOK, EmailProvider.OFFICE365]:
                return await self._test_outlook_connection(connection)
            elif connection.provider == EmailProvider.IMAP:
                return await self._test_imap_connection(connection)

        except Exception as e:
            logger.error(f"Connection test failed for {connection.id}: {e}")
            return False

        return False

    async def _test_gmail_connection(self, connection: EmailConnection) -> bool:
        """Test Gmail API connection"""
        try:
            access_token = self.decrypt_token(connection.access_token_encrypted)
            credentials = Credentials(access_token)

            service = build('gmail', 'v1', credentials=credentials)
            # Test by getting user profile
            profile = service.users().getProfile(userId='me').execute()
            return profile is not None

        except Exception as e:
            logger.error(f"Gmail connection test failed: {e}")
            return False

    async def _test_outlook_connection(self, connection: EmailConnection) -> bool:
        """Test Outlook/Graph API connection"""
        try:
            access_token = self.decrypt_token(connection.access_token_encrypted)

            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }

            # Test by getting user profile
            response = requests.get(
                'https://graph.microsoft.com/v1.0/me',
                headers=headers
            )
            return response.status_code == 200

        except Exception as e:
            logger.error(f"Outlook connection test failed: {e}")
            return False

    async def _test_imap_connection(self, connection: EmailConnection) -> bool:
        """Test IMAP connection (basic implementation)"""
        try:
            # This is a simplified implementation
            # In practice, you'd need proper IMAP server configuration
            # For now, just validate the email format
            if '@' not in connection.email_address:
                return False
            return True

        except Exception as e:
            logger.error(f"IMAP connection test failed: {e}")
            return False

    def get_user_connections(self, db: Session, user_id: str) -> List[EmailConnection]:
        """Get all email connections for a user"""
        result = await db.execute(query)
        return result.scalars().all()

    async def disconnect_email(self, db: Session, connection_id: str, user_id: str) -> bool:
        """Disconnect email connection"""
        connection = result = await db.execute(query)
        return result.scalars().all()

        if not connection:
            return False

        connection.is_active = False
        connection.sync_status = "disconnected"
        await db.commit()

        logger.info(f"Disconnected email connection {connection_id}")
        return True


# Global service instance
email_connector_service = EmailConnectorService()