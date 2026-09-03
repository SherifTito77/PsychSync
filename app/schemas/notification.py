"""
Notification Schemas

Minimal schemas for NotificationService to work with BaseService.
Note: NotificationService is primarily a sending service, not a CRUD service.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class NotificationBase(BaseModel):
    """Base notification schema"""

    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    user_id: UUID
    organization_id: UUID
    type: str
    title: str
    content: str
    notification_metadata: dict[str, Any] = {}
    priority: str = "normal"
    scheduled_at: datetime | None = None
    expires_at: datetime | None = None


class NotificationCreate(NotificationBase):
    """Schema for creating notifications"""

    pass


class NotificationUpdate(BaseModel):
    """Schema for updating notifications"""

    model_config = ConfigDict(from_attributes=True)

    status: str | None = None
    read_at: datetime | None = None
    sent_at: datetime | None = None
    error_message: str | None = None
    error_code: str | None = None


class NotificationResponse(NotificationBase):
    """Schema for notification responses"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    retry_count: int
    created_at: datetime
    updated_at: datetime
