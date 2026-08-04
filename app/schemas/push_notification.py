"""
Push Notification Schemas

NOTE: These schemas are for the Notification model used to track push notifications.
The PushNotificationToken model referenced in the original service does not exist yet.
TODO: Create PushNotificationToken model in app/db/models/notifications.py
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PushNotificationBase(BaseModel):
    """Base push notification schema"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    user_id: UUID
    organization_id: UUID
    type: str  # Notification type from NotificationType enum
    title: str
    content: str
    notification_metadata: dict[str, Any] = {}
    priority: str = "normal"
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None


class PushNotificationCreate(PushNotificationBase):
    """Schema for creating push notifications"""

    pass


class PushNotificationUpdate(BaseModel):
    """Schema for updating push notifications"""

    model_config = ConfigDict(from_attributes=True)

    status: str | None = None
    sent_at: datetime | None = None
    error_message: str | None = None
    error_code: str | None = None


class PushNotificationResponse(PushNotificationBase):
    """Schema for push notification responses"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    retry_count: int
    created_at: datetime
    updated_at: datetime
