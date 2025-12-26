# app/domain/events/user_events.py

"""
DOMAIN USER EVENTS
Domain events for user-related business operations

This module defines domain events that are raised when important
user-related business events occur in the system.

Author: Security Team
Version: 2.0 Enterprise Security
"""

import uuid
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class DomainEvent:
    """Base domain event class"""
    event_id: str
    event_type: str
    timestamp: datetime
    aggregate_id: str
    data: Dict[str, Any]

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class UserRegisteredEvent(DomainEvent):
    """Domain event raised when a new user is registered"""
    user_id: str
    email: str
    registration_time: datetime
    registration_source: str
    client_ip: Optional[str] = None
    organization_id: Optional[str] = None

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserRegistered"
        self.timestamp = self.registration_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "registration_source": self.registration_source,
            "client_ip": self.client_ip,
            "organization_id": self.organization_id
        }


@dataclass
class UserEmailVerifiedEvent(DomainEvent):
    """Domain event raised when a user verifies their email"""
    user_id: str
    email: str
    verification_time: datetime
    verification_method: str  # 'token', 'admin', etc.

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserEmailVerified"
        self.timestamp = self.verification_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "verification_method": self.verification_method
        }


@dataclass
class UserLoginEvent(DomainEvent):
    """Domain event raised when a user logs in"""
    user_id: str
    email: str
    login_time: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    login_method: str = "password"  # password, oauth, sso, etc.

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserLogin"
        self.timestamp = self.login_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "login_method": self.login_method
        }


@dataclass
class UserPasswordChangedEvent(DomainEvent):
    """Domain event raised when a user changes their password"""
    user_id: str
    email: str
    change_time: datetime
    change_reason: str  # 'user_request', 'admin_reset', 'security', etc.

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserPasswordChanged"
        self.timestamp = self.change_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "change_reason": self.change_reason
        }


@dataclass
class UserSuspendedEvent(DomainEvent):
    """Domain event raised when a user is suspended"""
    user_id: str
    email: str
    suspension_time: datetime
    suspension_reason: str
    suspended_by: Optional[str] = None  # User ID of admin who suspended

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserSuspended"
        self.timestamp = self.suspension_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "suspension_reason": self.suspension_reason,
            "suspended_by": self.suspended_by
        }


@dataclass
class UserActivatedEvent(DomainEvent):
    """Domain event raised when a suspended user is reactivated"""
    user_id: str
    email: str
    activation_time: datetime
    activation_reason: str
    activated_by: Optional[str] = None  # User ID of admin who activated

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserActivated"
        self.timestamp = self.activation_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "activation_reason": self.activation_reason,
            "activated_by": self.activated_by
        }


@dataclass
class UserUpdatedProfileEvent(DomainEvent):
    """Domain event raised when a user updates their profile"""
    user_id: str
    email: str
    update_time: datetime
    updated_fields: Dict[str, Any]

    def __post_init__(self):
        self.event_id = str(uuid.uuid4())
        self.event_type = "UserUpdatedProfile"
        self.timestamp = self.update_time
        self.aggregate_id = self.user_id
        self.data = {
            "user_id": self.user_id,
            "email": self.email,
            "updated_fields": self.updated_fields
        }