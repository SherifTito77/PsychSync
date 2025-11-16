# app/services/email_connection_service.py
"""
Email Connection CRUD Service
Handles database operations for email connections
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, func

from app.db.models.email_connection import EmailConnection, EmailMetadata, EmailProvider
from app.db.models.user import User


class EmailConnectionService:
    """Service for managing email connections and metadata"""

    @staticmethod
    async def get_connection_by_email_and_provider(
        db: Session,
        user_id: str,
        email_address: str,
        provider: EmailProvider
    ) -> Optional[EmailConnection]:
        """Get existing email connection by email and provider"""
        return db.query(EmailConnection).filter(
            and_(
                EmailConnection.user_id == user_id,
                EmailConnection.email_address == email_address,
                EmailConnection.provider == provider
            )
        ).first()

    @staticmethod
    async def get_connection_by_email(
        db: Session,
        user_id: str,
        email_address: str
    ) -> Optional[EmailConnection]:
        """Get existing email connection by email address (for simple connections)"""
        return db.query(EmailConnection).filter(
            and_(
                EmailConnection.user_id == user_id,
                EmailConnection.email_address == email_address,
                EmailConnection.is_active == True
            )
        ).first()

    @staticmethod
    async def get_connection_by_id(
        db: Session,
        user_id: str,
        connection_id: str
    ) -> Optional[EmailConnection]:
        """Get email connection by ID"""
        return db.query(EmailConnection).filter(
            and_(
                EmailConnection.id == connection_id,
                EmailConnection.user_id == user_id
            )
        ).first()

    @staticmethod
    async def get_user_connections(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[EmailConnection]:
        """Get all email connections for a user"""
        return db.query(EmailConnection).filter(
            EmailConnection.user_id == user_id
        ).offset(skip).limit(limit).all()

    @staticmethod
    async def create_connection(
        db: Session,
        user_id: str,
        provider: EmailProvider,
        email_address: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        account_name: Optional[str] = None,
        privacy_settings: Optional[Dict[str, Any]] = None
    ) -> EmailConnection:
        """Create a new email connection"""
        connection = EmailConnection(
            user_id=user_id,
            provider=provider,
            email_address=email_address,
            access_token=access_token,
            refresh_token=refresh_token,
            account_name=account_name,
            privacy_settings=privacy_settings or {},
            is_active=True,
            sync_status="pending",
            created_at=datetime.utcnow()
        )

        db.add(connection)
        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def update_connection(
        db: Session,
        connection_id: str,
        user_id: str,
        **updates
    ) -> Optional[EmailConnection]:
        """Update an existing email connection"""
        connection = await EmailConnectionService.get_connection_by_id(db, user_id, connection_id)
        if not connection:
            return None

        for key, value in updates.items():
            if hasattr(connection, key):
                setattr(connection, key, value)

        connection.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(connection)
        return connection

    @staticmethod
    async def delete_connection(
        db: Session,
        connection_id: str,
        user_id: str
    ) -> bool:
        """Delete an email connection"""
        connection = await EmailConnectionService.get_connection_by_id(db, user_id, connection_id)
        if not connection:
            return False

        db.delete(connection)
        await db.commit()
        return True

    @staticmethod
    async def get_connection_stats(
        db: Session,
        user_id: str,
        connection_id: str
    ) -> Dict[str, int]:
        """Get statistics for an email connection"""
        total_emails = db.query(EmailMetadata).filter(
            and_(
                EmailMetadata.connection_id == connection_id,
                EmailMetadata.user_id == user_id
            )
        ).count()

        recent_emails = db.query(EmailMetadata).filter(
            and_(
                EmailMetadata.connection_id == connection_id,
                EmailMetadata.user_id == user_id,
                EmailMetadata.received_at >= datetime.utcnow() - timedelta(days=7)
            )
        ).count()

        internal_emails = db.query(EmailMetadata).filter(
            and_(
                EmailMetadata.connection_id == connection_id,
                EmailMetadata.user_id == user_id,
                EmailMetadata.email_type == "internal"
            )
        ).count()

        return {
            "total_emails": total_emails,
            "recent_emails": recent_emails,
            "internal_emails": internal_emails
        }

    @staticmethod
    async def get_connections_with_stats(
        db: Session,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get connections with their statistics"""
        connections = await EmailConnectionService.get_user_connections(db, user_id, skip, limit)

        result = []
        for connection in connections:
            stats = await EmailConnectionService.get_connection_stats(db, user_id, connection.id)
            result.append({
                "connection": connection,
                "stats": stats
            })

        return result


# Create service instance
email_connection_service = EmailConnectionService()