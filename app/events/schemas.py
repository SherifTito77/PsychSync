"""
Event Schemas for Event-Driven Architecture

Defines all event types published/consumed in the system.
Events follow CloudEvents specification for interoperability.

Event Categories:
1. Assessment Events: Assessment lifecycle events
2. User Events: User account and profile events
3. Team Events: Team management events
4. Organization Events: Organization-level events
5. System Events: Platform operational events

Created: 2025-01-12
Author: Architecture Team
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, validator


class EventType(str, Enum):
    """Standard event types"""

    # Assessment events
    ASSESSMENT_STARTED = "assessment.started"
    ASSESSMENT_COMPLETED = "assessment.completed"
    ASSESSMENT_ABORTED = "assessment.aborted"
    ASSESSMENT_EXPIRED = "assessment.expired"

    # User events
    USER_REGISTERED = "user.registered"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"
    USER_PROFILE_UPDATED = "user.profile_updated"

    # Team events
    TEAM_CREATED = "team.created"
    TEAM_UPDATED = "team.updated"
    TEAM_DELETED = "team.deleted"
    TEAM_MEMBER_ADDED = "team.member_added"
    TEAM_MEMBER_REMOVED = "team.member_removed"
    TEAM_ROLE_CHANGED = "team.role_changed"

    # Organization events
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"
    ORGANIZATION_SUSPENDED = "organization.suspended"

    # Analytics events
    ANALYTICS_GENERATED = "analytics.generated"
    ANALYTICS_VIEWED = "analytics.viewed"

    # Billing events
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_UPDATED = "subscription.updated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    INVOICE_GENERATED = "invoice.generated"
    INVOICE_PAID = "invoice.paid"

    # Notification events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_FAILED = "notification.failed"

    # System events
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE_STARTED = "system.maintenance_started"
    SYSTEM_MAINTENANCE_ENDED = "system.maintenance_ended"


class EventSource(str, Enum):
    """Event sources (producers)"""

    ASSESSMENT_SERVICE = "/assessment-service"
    USER_SERVICE = "/user-service"
    TEAM_SERVICE = "/team-service"
    ORGANIZATION_SERVICE = "/organization-service"
    ANALYTICS_SERVICE = "/analytics-service"
    BILLING_SERVICE = "/billing-service"
    NOTIFICATION_SERVICE = "/notification-service"
    API_GATEWAY = "/api-gateway"


class CloudEvent(BaseModel):
    """
    Base CloudEvent-compliant event schema.

    Follows CloudEvents specification: https://cloudevents.io/
    """

    # Required attributes
    id: str = Field(default_factory=lambda: str(uuid4()))
    source: EventSource = Field(description="Event producer")
    specversion: str = Field(default="1.0", description="CloudEvents spec version")
    type: EventType = Field(description="Event type")

    # Optional attributes
    datacontenttype: str = Field(
        default="application/json", description="Data content type"
    )
    dataschema: Optional[str] = Field(None, description="Data schema URL")
    subject: Optional[str] = Field(None, description="Event subject (context)")

    # Event metadata
    time: datetime = Field(
        default_factory=datetime.utcnow, description="Event timestamp"
    )
    correlation_id: Optional[str] = Field(
        None, description="Correlation ID for tracing"
    )
    causation_id: Optional[str] = Field(
        None, description="Causation ID (event that caused this)"
    )
    tenant_id: Optional[str] = Field(None, description="Tenant ID for multi-tenancy")

    # Event payload
    data: Dict[str, Any] = Field(default_factory=dict, description="Event payload")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }

    @validator("correlation_id", always=True)
    def set_correlation_id(cls, v, values):
        """Set correlation_id to id if not provided"""
        if v is None and "id" in values:
            return values["id"]
        return v


# ==================== ASSESSMENT EVENTS ====================


class AssessmentStartedEvent(CloudEvent):
    """Event emitted when user starts an assessment"""

    type: EventType = EventType.ASSESSMENT_STARTED
    source: EventSource = EventSource.ASSESSMENT_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "assessment_id": "UUID",
            "user_id": "UUID",
            "team_id": "UUID (optional)",
            "framework_code": "str (e.g., MBTI, BigFive)",
            "started_at": "ISO datetime",
        },
    )


class AssessmentCompletedEvent(CloudEvent):
    """Event emitted when user completes an assessment"""

    type: EventType = EventType.ASSESSMENT_COMPLETED
    source: EventSource = EventSource.ASSESSMENT_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "assessment_id": "UUID",
            "user_id": "UUID",
            "team_id": "UUID (optional)",
            "framework_code": "str",
            "started_at": "ISO datetime",
            "completed_at": "ISO datetime",
            "score": "float",
            "max_score": "float",
            "results": "dict (assessment-specific results)",
        },
    )


# ==================== USER EVENTS ====================


class UserRegisteredEvent(CloudEvent):
    """Event emitted when new user registers"""

    type: EventType = EventType.USER_REGISTERED
    source: EventSource = EventSource.USER_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "user_id": "UUID",
            "email": "str",
            "full_name": "str",
            "organization_id": "UUID",
            "registration_method": "str (email, sso, etc.)",
            "registered_at": "ISO datetime",
        },
    )


class UserActivatedEvent(CloudEvent):
    """Event emitted when user account is activated"""

    type: EventType = EventType.USER_ACTIVATED
    source: EventSource = EventSource.USER_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "user_id": "UUID",
            "email": "str",
            "activated_at": "ISO datetime",
            "activation_method": "str (email_verification, admin_approval)",
        },
    )


# ==================== TEAM EVENTS ====================


class TeamCreatedEvent(CloudEvent):
    """Event emitted when team is created"""

    type: EventType = EventType.TEAM_CREATED
    source: EventSource = EventSource.TEAM_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "team_id": "UUID",
            "name": "str",
            "organization_id": "UUID",
            "created_by": "UUID (user_id)",
            "created_at": "ISO datetime",
        },
    )


class TeamMemberAddedEvent(CloudEvent):
    """Event emitted when member is added to team"""

    type: EventType = EventType.TEAM_MEMBER_ADDED
    source: EventSource = EventSource.TEAM_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "team_id": "UUID",
            "user_id": "UUID",
            "role": "str (member, lead, admin)",
            "added_by": "UUID (user_id)",
            "added_at": "ISO datetime",
        },
    )


# ==================== ORGANIZATION EVENTS ====================


class OrganizationCreatedEvent(CloudEvent):
    """Event emitted when organization is created"""

    type: EventType = EventType.ORGANIZATION_CREATED
    source: EventSource = EventSource.ORGANIZATION_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "organization_id": "UUID",
            "name": "str",
            "tier": "str (smb, enterprise, trial)",
            "created_by": "UUID (user_id)",
            "created_at": "ISO datetime",
        },
    )


# ==================== ANALYTICS EVENTS ====================


class AnalyticsGeneratedEvent(CloudEvent):
    """Event emitted when analytics are generated"""

    type: EventType = EventType.ANALYTICS_GENERATED
    source: EventSource = EventSource.ANALYTICS_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "analytics_id": "UUID",
            "entity_type": "str (user, team, organization)",
            "entity_id": "UUID",
            "analytics_type": "str (personality, performance, engagement)",
            "generated_at": "ISO datetime",
            "summary": "dict",
        },
    )


# ==================== BILLING EVENTS ====================


class InvoiceGeneratedEvent(CloudEvent):
    """Event emitted when invoice is generated"""

    type: EventType = EventType.INVOICE_GENERATED
    source: EventSource = EventSource.BILLING_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "invoice_id": "UUID",
            "organization_id": "UUID",
            "amount": "float",
            "currency": "str",
            "period_start": "ISO date",
            "period_end": "ISO date",
            "generated_at": "ISO datetime",
        },
    )


# ==================== NOTIFICATION EVENTS ====================


class NotificationSentEvent(CloudEvent):
    """Event emitted when notification is sent"""

    type: EventType = EventType.NOTIFICATION_SENT
    source: EventSource = EventSource.NOTIFICATION_SERVICE

    data: Dict[str, Any] = Field(
        ...,
        description={
            "notification_id": "UUID",
            "recipient_id": "UUID",
            "type": "str (email, sms, push, in_app)",
            "channel": "str",
            "subject": "str",
            "sent_at": "ISO datetime",
        },
    )


# ==================== SYSTEM EVENTS ====================


class SystemErrorEvent(CloudEvent):
    """Event emitted when system error occurs"""

    type: EventType = EventType.SYSTEM_ERROR
    source: EventSource = EventSource.API_GATEWAY

    data: Dict[str, Any] = Field(
        ...,
        description={
            "error_code": "str",
            "error_message": "str",
            "service": "str",
            "request_id": "str",
            "timestamp": "ISO datetime",
            "stack_trace": "str (optional)",
        },
    )


# ==================== EVENT FACTORY ====================


class EventFactory:
    """
    Factory for creating standardized events.

    Usage:
        event = EventFactory.assessment_started(
            assessment_id="123",
            user_id="456",
            framework_code="MBTI"
        )
    """

    @staticmethod
    def assessment_started(
        assessment_id: str,
        user_id: str,
        framework_code: str,
        team_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> AssessmentStartedEvent:
        """Create assessment.started event"""
        return AssessmentStartedEvent(
            tenant_id=tenant_id,
            data={
                "assessment_id": assessment_id,
                "user_id": user_id,
                "team_id": team_id,
                "framework_code": framework_code,
                "started_at": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def assessment_completed(
        assessment_id: str,
        user_id: str,
        framework_code: str,
        score: float,
        max_score: float,
        results: Dict[str, Any],
        team_id: Optional[str] = None,
        started_at: Optional[datetime] = None,
        tenant_id: Optional[str] = None,
    ) -> AssessmentCompletedEvent:
        """Create assessment.completed event"""
        return AssessmentCompletedEvent(
            tenant_id=tenant_id,
            data={
                "assessment_id": assessment_id,
                "user_id": user_id,
                "team_id": team_id,
                "framework_code": framework_code,
                "started_at": (started_at or datetime.utcnow()).isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "score": score,
                "max_score": max_score,
                "results": results,
            },
        )

    @staticmethod
    def user_registered(
        user_id: str,
        email: str,
        full_name: str,
        organization_id: str,
        registration_method: str = "email",
        tenant_id: Optional[str] = None,
    ) -> UserRegisteredEvent:
        """Create user.registered event"""
        return UserRegisteredEvent(
            tenant_id=tenant_id,
            data={
                "user_id": user_id,
                "email": email,
                "full_name": full_name,
                "organization_id": organization_id,
                "registration_method": registration_method,
                "registered_at": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def team_created(
        team_id: str,
        name: str,
        organization_id: str,
        created_by: str,
        tenant_id: Optional[str] = None,
    ) -> TeamCreatedEvent:
        """Create team.created event"""
        return TeamCreatedEvent(
            tenant_id=tenant_id,
            data={
                "team_id": team_id,
                "name": name,
                "organization_id": organization_id,
                "created_by": created_by,
                "created_at": datetime.utcnow().isoformat(),
            },
        )

    @staticmethod
    def analytics_generated(
        analytics_id: str,
        entity_type: str,
        entity_id: str,
        analytics_type: str,
        summary: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> AnalyticsGeneratedEvent:
        """Create analytics.generated event"""
        return AnalyticsGeneratedEvent(
            tenant_id=tenant_id,
            data={
                "analytics_id": analytics_id,
                "entity_type": entity_type,
                "entity_id": entity_id,
                "analytics_type": analytics_type,
                "generated_at": datetime.utcnow().isoformat(),
                "summary": summary,
            },
        )
