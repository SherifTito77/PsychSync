"""
PsychSync Mobile API Bridge

This module provides the API bridge for mobile applications with:
- Mobile-first API endpoints
- Push notification services
- Offline sync capabilities
- Mobile-specific authentication
- Performance optimization for mobile networks
- Battery-efficient data transfer
- Mobile analytics integration
"""
import os

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

import aiohttp
import asyncpg
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field

from app.core.advanced_database import get_database_connection
from app.core.feature_flags import get_feature_flag_manager, UserContext

logger = logging.getLogger(__name__)

# Mobile API Router
mobile_router = APIRouter(prefix="/api/v2/mobile", tags=["mobile"])
security = HTTPBearer()


class MobilePlatform(Enum):
    IOS = "ios"
    ANDROID = "android"
    WEB = "web"


class PushNotificationType(Enum):
    ASSESSMENT_REMINDER = "assessment_reminder"
    TEAM_UPDATE = "team_update"
    INSIGHT_READY = "insight_ready"
    MILESTONE_ACHIEVED = "milestone_achieved"
    ANNOUNCEMENT = "announcement"
    SYSTEM_UPDATE = "system_update"


@dataclass
class MobileDeviceInfo:
    """Mobile device information"""
    device_id: str
    platform: MobilePlatform
    app_version: str
    os_version: str
    push_token: Optional[str] = None
    device_model: Optional[str] = None
    manufacturer: Optional[str] = None
    language: str = "en"
    timezone: str = "UTC"


class MobileUser(BaseModel):
    """Mobile user model"""
    user_id: str
    email: str
    full_name: str
    organization_id: str
    role: str
    created_at: datetime
    last_login: Optional[datetime] = None
    preferences: Dict[str, Any] = Field(default_factory=dict)


class PushNotificationMessage(BaseModel):
    """Push notification message"""
    user_id: str
    title: str
    body: str
    type: PushNotificationType
    data: Dict[str, Any] = Field(default_factory=dict)
    priority: str = "normal"  # normal, high
    ttl: Optional[int] = None  # Time to live in seconds


class OfflineSyncData(BaseModel):
    """Offline synchronization data"""
    user_id: str
    device_id: str
    sync_type: str  # full, incremental
    last_sync_timestamp: Optional[datetime] = None
    data_hash: str
    compressed_data: bytes
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MobileAPIBridge:
    """Mobile API bridge service"""

    def __init__(self, database_url: str, onesignal_app_id: str, onesignal_api_key: str):
        self.database_url = database_url
        self.onesignal_app_id = onesignal_app_id
        self.onesignal_api_key = onesignal_api_key
        self.db_pool = None

    async def initialize(self):
        """Initialize mobile API bridge"""
        self.db_pool = await asyncpg.create_pool(
            self.database_url,
            min_size=5,
            max_size=20,
            command_timeout=30
        )
        logger.info("🚀 Mobile API bridge initialized")

    async def register_device(self, user_id: str, device_info: MobileDeviceInfo) -> Dict[str, Any]:
        """Register mobile device"""
        try:
            async with self.db_pool.acquire() as conn:
                # Check if device already exists
                existing_device = await conn.fetchrow(
                    "SELECT id FROM mobile_devices WHERE user_id = $1 AND device_id = $2",
                    user_id, device_info.device_id
                )

                if existing_device:
                    # Update existing device
                    await conn.execute("""
                        UPDATE mobile_devices SET
                            platform = $1,
                            app_version = $2,
                            os_version = $3,
                            push_token = $4,
                            device_model = $5,
                            manufacturer = $6,
                            language = $7,
                            timezone = $8,
                            updated_at = NOW()
                        WHERE user_id = $9 AND device_id = $10
                    """, device_info.platform.value, device_info.app_version,
                        device_info.os_version, device_info.push_token,
                        device_info.device_model, device_info.manufacturer,
                        device_info.language, device_info.timezone,
                        user_id, device_info.device_id)
                else:
                    # Register new device
                    await conn.execute("""
                        INSERT INTO mobile_devices (
                            user_id, device_id, platform, app_version, os_version,
                            push_token, device_model, manufacturer, language, timezone,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                    """, user_id, device_info.device_id, device_info.platform.value,
                        device_info.app_version, device_info.os_version, device_info.push_token,
                        device_info.device_model, device_info.manufacturer,
                        device_info.language, device_info.timezone)

                return {
                    "status": "success",
                    "message": "Device registered successfully",
                    "device_id": device_info.device_id
                }

        except Exception as e:
            logger.error(f"Failed to register device for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to register device")

    async def send_push_notification(self, notification: PushNotificationMessage) -> bool:
        """Send push notification via OneSignal"""
        try:
            # Get user's devices
            async with self.db_pool.acquire() as conn:
                devices = await conn.fetch(
                    "SELECT push_token, platform FROM mobile_devices WHERE user_id = $1 AND push_token IS NOT NULL",
                    notification.user_id
                )

            if not devices:
                logger.warning(f"No devices found for user {notification.user_id}")
                return False

            # Prepare OneSignal notification
            onesignal_data = {
                "app_id": self.onesignal_app_id,
                "headings": {"en": notification.title},
                "contents": {"en": notification.body},
                "data": notification.data,
                "priority": notification.priority,
                "ttl": notification.ttl,
                "content_available": True
            }

            # Add platform-specific settings
            include_player_ids = []
            for device in devices:
                if device['push_token']:
                    include_player_ids.append(device['push_token'])

            if include_player_ids:
                onesignal_data["include_player_ids"] = include_player_ids

                # iOS specific settings
                if any(device['platform'] == 'ios' for device in devices):
                    onesignal_data["ios_badgeType"] = "Increase"
                    onesignal_data["ios_badgeCount"] = 1

                # Android specific settings
                if any(device['platform'] == 'android' for device in devices):
                    onesignal_data["android_channel_id"] = "psychsync_notifications"

                # Send notification
                headers = {
                    "Content-Type": "application/json; charset=utf-8",
                    "Authorization": f"Basic {self.onesignal_api_key}"
                }

                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        "https://onesignal.com/api/v1/notifications",
                        headers=headers,
                        json=onesignal_data
                    ) as response:
                        if response.status == 200:
                            result = await response.json()
                            logger.info(f"Push notification sent to {len(include_player_ids)} devices for user {notification.user_id}")
                            return True
                        else:
                            error_text = await response.text()
                            logger.error(f"Failed to send push notification: {error_text}")
                            return False

            return False

        except Exception as e:
            logger.error(f"Failed to send push notification: {e}")
            return False

    async def get_mobile_user_data(self, user_id: str, device_id: str, last_sync: Optional[datetime] = None) -> Dict[str, Any]:
        """Get mobile user data for offline sync"""
        try:
            async with self.db_pool.acquire() as conn:
                # Get user profile
                user = await conn.fetchrow("""
                    SELECT u.id, u.email, u.full_name, u.organization_id, u.role, u.created_at,
                           u.last_login, u.preferences
                    FROM users u
                    WHERE u.id = $1 AND u.is_active = true
                """, user_id)

                if not user:
                    raise HTTPException(status_code=404, detail="User not found")

                # Get user's teams
                teams = await conn.fetch("""
                    SELECT t.id, t.name, t.description, tm.role as user_role
                    FROM teams t
                    JOIN team_members tm ON t.id = tm.team_id
                    WHERE tm.user_id = $1 AND tm.is_active = true AND t.is_active = true
                """, user_id)

                # Get recent assessments (since last sync)
                assessments_query = """
                    SELECT a.id, a.title, a.category, a.status, a.created_at, a.updated_at,
                           ar.score, ar.completed_at
                    FROM assessments a
                    LEFT JOIN assessment_responses ar ON a.id = ar.assessment_id AND ar.user_id = $1
                    WHERE a.organization_id = $2 AND (a.created_by_id = $1 OR ar.user_id = $1)
                """

                if last_sync:
                    assessments_query += " AND a.updated_at > $3"
                    assessments = await conn.fetch(assessments_query, user_id, user['organization_id'], last_sync)
                else:
                    assessments = await conn.fetch(assessments_query, user_id, user['organization_id'])

                # Get user's notifications
                notifications_query = """
                    SELECT id, type, title, content, data, created_at, read_at
                    FROM notifications
                    WHERE user_id = $1
                """

                if last_sync:
                    notifications_query += " AND created_at > $2"
                    notifications = await conn.fetch(notifications_query, user_id, last_sync)
                else:
                    notifications_query += " ORDER BY created_at DESC LIMIT 50"
                    notifications = await conn.fetch(notifications_query, user_id)

                # Get user preferences for mobile
                mobile_preferences = await conn.fetchrow("""
                    SELECT push_enabled, in_app_enabled, quiet_hours_enabled,
                           quiet_hours_start, quiet_hours_end
                    FROM notification_preferences
                    WHERE user_id = $1
                """, user_id)

                return {
                    "user": {
                        "id": user['id'],
                        "email": user['email'],
                        "full_name": user['full_name'],
                        "organization_id": user['organization_id'],
                        "role": user['role'],
                        "preferences": user['preferences'] or {}
                    },
                    "teams": [
                        {
                            "id": team['id'],
                            "name": team['name'],
                            "description": team['description'],
                            "role": team['user_role']
                        } for team in teams
                    ],
                    "assessments": [
                        {
                            "id": assessment['id'],
                            "title": assessment['title'],
                            "category": assessment['category'],
                            "status": assessment['status'],
                            "score": float(assessment['score']) if assessment['score'] else None,
                            "completed_at": assessment['completed_at'].isoformat() if assessment['completed_at'] else None,
                            "updated_at": assessment['updated_at'].isoformat() if assessment['updated_at'] else None
                        } for assessment in assessments
                    ],
                    "notifications": [
                        {
                            "id": notification['id'],
                            "type": notification['type'],
                            "title": notification['title'],
                            "content": notification['content'],
                            "data": notification['data'],
                            "created_at": notification['created_at'].isoformat(),
                            "read_at": notification['read_at'].isoformat() if notification['read_at'] else None
                        } for notification in notifications
                    ],
                    "preferences": {
                        "push_enabled": mobile_preferences['push_enabled'] if mobile_preferences else True,
                        "in_app_enabled": mobile_preferences['in_app_enabled'] if mobile_preferences else True,
                        "quiet_hours_enabled": mobile_preferences['quiet_hours_enabled'] if mobile_preferences else False,
                        "quiet_hours_start": mobile_preferences['quiet_hours_start'] if mobile_preferences else "22:00",
                        "quiet_hours_end": mobile_preferences['quiet_hours_end'] if mobile_preferences else "08:00"
                    },
                    "sync_timestamp": datetime.now(timezone.utc).isoformat()
                }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get mobile user data for {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get user data")

    async def sync_offline_data(self, sync_data: OfflineSyncData) -> Dict[str, Any]:
        """Process offline data synchronization"""
        try:
            # Validate data integrity
            if not sync_data.compressed_data:
                raise HTTPException(status_code=400, detail="No data provided")

            # Decompress and validate data
            import zlib
            try:
                json_data = zlib.decompress(sync_data.compressed_data).decode('utf-8')
                import json
                offline_data = json.loads(json_data)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Invalid data format: {e}")

            async with self.db_pool.acquire() as conn:
                # Start transaction
                async with conn.transaction():
                    # Process assessments data
                    if 'assessments' in offline_data:
                        for assessment in offline_data['assessments']:
                            await self._process_offline_assessment(conn, sync_data.user_id, assessment)

                    # Process responses data
                    if 'responses' in offline_data:
                        for response in offline_data['responses']:
                            await self._process_offline_response(conn, sync_data.user_id, response)

                    # Update sync timestamp
                    await conn.execute("""
                        UPDATE mobile_devices
                        SET last_sync_timestamp = NOW(), updated_at = NOW()
                        WHERE user_id = $1 AND device_id = $2
                    """, sync_data.user_id, sync_data.device_id)

                    # Log sync activity
                    await conn.execute("""
                        INSERT INTO mobile_sync_logs (
                            user_id, device_id, sync_type, data_size, status, created_at
                        ) VALUES ($1, $2, $3, $4, 'success', NOW())
                    """, sync_data.user_id, sync_data.device_id,
                        sync_data.sync_type, len(sync_data.compressed_data))

            return {
                "status": "success",
                "processed_items": len(offline_data.get('assessments', [])) + len(offline_data.get('responses', [])),
                "sync_timestamp": datetime.now(timezone.utc).isoformat()
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to sync offline data for user {sync_data.user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to sync offline data")

    async def _process_offline_assessment(self, conn, user_id: str, assessment_data: Dict[str, Any]):
        """Process offline assessment data"""
        # Implementation depends on your assessment schema
        pass

    async def _process_offline_response(self, conn, user_id: str, response_data: Dict[str, Any]):
        """Process offline response data"""
        # Implementation depends on your response schema
        pass

    async def get_mobile_analytics(self, user_id: str, device_id: str, metrics: List[str]) -> Dict[str, Any]:
        """Get mobile analytics data"""
        try:
            async with self.db_pool.acquire() as conn:
                analytics_data = {}

                # App usage metrics
                if 'usage' in metrics:
                    usage_data = await conn.fetchrow("""
                        SELECT COUNT(*) as total_sessions,
                               AVG(duration_seconds) as avg_session_duration,
                               MAX(session_timestamp) as last_session
                        FROM mobile_sessions
                        WHERE user_id = $1 AND device_id = $2
                    """, user_id, device_id)

                    analytics_data['usage'] = dict(usage_data) if usage_data else {}

                # Feature usage metrics
                if 'features' in metrics:
                    feature_data = await conn.fetch("""
                        SELECT feature_name, COUNT(*) as usage_count,
                               MAX(used_at) as last_used
                        FROM mobile_feature_usage
                        WHERE user_id = $1 AND device_id = $2
                        GROUP BY feature_name
                    """, user_id, device_id)

                    analytics_data['features'] = [dict(row) for row in feature_data]

                # Performance metrics
                if 'performance' in metrics:
                    perf_data = await conn.fetchrow("""
                        SELECT AVG(load_time_ms) as avg_load_time,
                               AVG(api_response_time_ms) as avg_response_time,
                               COUNT(*) as total_requests,
                               COUNT(CASE WHEN error_occurred THEN 1 END) as error_count
                        FROM mobile_performance_logs
                        WHERE user_id = $1 AND device_id = $2
                          AND created_at >= NOW() - INTERVAL '7 days'
                    """, user_id, device_id)

                    analytics_data['performance'] = dict(perf_data) if perf_data else {}

                return analytics_data

        except Exception as e:
            logger.error(f"Failed to get mobile analytics for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get analytics")

    async def close(self):
        """Close mobile API bridge"""
        if self.db_pool:
            await self.db_pool.close()


# Mobile API endpoints
@mobile_router.post("/register-device")
async def register_device(
    device_info: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_bridge: MobileAPIBridge = Depends()
):
    """Register mobile device"""
    return await api_bridge.register_device(
        user_id=extract_user_id(credentials.credentials),
        device_info=MobileDeviceInfo(**device_info)
    )


@mobile_router.get("/sync-data")
async def get_sync_data(
    last_sync: Optional[str] = None,
    device_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_bridge: MobileAPIBridge = Depends()
):
    """Get data for offline synchronization"""
    user_id = extract_user_id(credentials.credentials)
    last_sync_dt = datetime.fromisoformat(last_sync) if last_sync else None

    return await api_bridge.get_mobile_user_data(
        user_id=user_id,
        device_id=device_id,
        last_sync=last_sync_dt
    )


@mobile_router.post("/sync-offline")
async def sync_offline_data(
    sync_data: OfflineSyncData,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_bridge: MobileAPIBridge = Depends()
):
    """Synchronize offline data"""
    return await api_bridge.sync_offline_data(sync_data)


@mobile_router.get("/analytics")
async def get_analytics(
    metrics: str = "usage,performance,features",
    device_id: str = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_bridge: MobileAPIBridge = Depends()
):
    """Get mobile analytics"""
    return await api_bridge.get_mobile_analytics(
        user_id=extract_user_id(credentials.credentials),
        device_id=device_id,
        metrics=metrics.split(',')
    )


@mobile_router.post("/send-notification")
async def send_notification(
    notification: PushNotificationMessage,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    api_bridge: MobileAPIBridge = Depends()
):
    """Send push notification"""
    success = await api_bridge.send_push_notification(notification)
    return {"status": "sent" if success else "failed"}


def extract_user_id(token: str) -> str:
    """Extract user ID from JWT token"""
    # Implementation depends on your JWT handling
    return "user_id_placeholder"  # Replace with actual implementation


# Initialize mobile API bridge
mobile_api_bridge = MobileAPIBridge(
    database_url=os.getenv("DATABASE_URL"),
    onesignal_app_id=os.getenv("ONESIGNAL_APP_ID"),
    onesignal_api_key=os.getenv("ONESIGNAL_API_KEY")
)
