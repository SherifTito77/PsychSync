"""
Health Monitoring WebSocket Endpoint

Provides real-time health monitoring updates via WebSocket connections.
Features:
- Live health risk updates
- Automated intervention alerts
- Biometric data notifications
- Stress level changes
- Connection heartbeat and reconnection handling
"""

import json
import logging
from datetime import datetime
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
# from sqlalchemy.orm import Session  # Replaced with AsyncSession
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.db.models.user import User
from app.services.health.stress_monitoring_service import (
    StressMonitoringService,
    HealthRiskIndicators,
)

logger = logging.getLogger(__name__)

# Create WebSocket router
ws_router = APIRouter(tags=["health-monitoring-ws"])


class ConnectionManager:
    """
    Manages WebSocket connections for health monitoring
    """

    def __init__(self):
        # Store active connections: {user_id: {websocket_ids}}
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store WebSocket metadata: {websocket_id: {user_id, connected_at}}
        self.connection_metadata: Dict[WebSocket, Dict] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)
        self.connection_metadata[websocket] = {
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"WebSocket connected for user {user_id}")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection_established",
            "message": "WebSocket connection established",
            "timestamp": datetime.utcnow().isoformat(),
        })

    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            # Clean up empty user entries
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

        logger.info(f"WebSocket disconnected for user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str):
        """Send a message to a specific user's connections"""
        if user_id in self.active_connections:
            disconnected = set()
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send message to user {user_id}: {e}")
                    disconnected.add(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected users"""
        all_disconnected = set()
        for user_id, connections in self.active_connections.items():
            for connection in connections:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to broadcast to user {user_id}: {e}")
                    all_disconnected.add((connection, user_id))

        # Clean up disconnected connections
        for connection, user_id in all_disconnected:
            self.disconnect(connection, user_id)

    def get_connection_count(self, user_id: str = None) -> int:
        """Get the number of active connections"""
        if user_id:
            return len(self.active_connections.get(user_id, set()))
        return sum(len(conns) for conns in self.active_connections.values())


# Global connection manager instance
manager = ConnectionManager()


@ws_router.websocket("/ws/health-monitoring")
async def websocket_health_monitoring(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    WebSocket endpoint for real-time health monitoring updates

    Connects clients to receive live updates:
    - Health risk changes
    - Stress level updates
    - Intervention alerts
    - Biometric data notifications

    Query Parameters:
    - token: JWT authentication token (required)

    Message Types:
    - connection_established: Connection confirmation
    - health_update: Health risk data update
    - health_alert: Automated intervention alert
    - heartbeat: Connection keepalive
    - error: Error messages
    """

    # Verify user authentication
    try:
        # Import auth dependency to verify token
        from app.services.security import verify_token
        payload = verify_token(token, db)
        user_id = payload.get("sub")

        if not user_id:
            await websocket.close(code=4001, reason="Invalid token: missing user_id")
            return

    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        await websocket.close(code=4001, reason="Authentication failed")
        return

    # Establish connection
    await manager.connect(websocket, user_id)

    try:
        # Send initial health data
        monitoring_service = StressMonitoringService(db)
        try:
            health_risks = await monitoring_service.analyze_health_risks(
                user_id=user_id,
                organization_id=None,  # Will be fetched from user
                time_window_days=7
            )

            await websocket.send_json({
                "type": "health_update",
                "data": {
                    "user_id": user_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "stress_level": health_risks.stress_level.value,
                    "burnout_stage": health_risks.burnout_stage.value,
                    "cardiovascular_risk_score": health_risks.cardiovascular_risk_score,
                    "mental_health_risk": health_risks.mental_health_risk,
                }
            })
        except Exception as e:
            logger.error(f"Failed to fetch initial health data: {e}")

        # Keep connection alive and listen for client messages
        while True:
            data = await websocket.receive_text()

            try:
                message = json.loads(data)

                # Handle different message types from client
                if message.get("type") == "heartbeat":
                    # Respond to heartbeat
                    await websocket.send_json({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                elif message.get("type") == "request_update":
                    # Client requests fresh health data
                    try:
                        health_risks = await monitoring_service.analyze_health_risks(
                            user_id=user_id,
                            organization_id=None,
                            time_window_days=message.get("time_window_days", 7)
                        )

                        await websocket.send_json({
                            "type": "health_update",
                            "data": {
                                "user_id": user_id,
                                "timestamp": datetime.utcnow().isoformat(),
                                "stress_level": health_risks.stress_level.value,
                                "burnout_stage": health_risks.burnout_stage.value,
                                "cardiovascular_risk_score": health_risks.cardiovascular_risk_score,
                                "mental_health_risk": health_risks.mental_health_risk,
                            }
                        })
                    except Exception as e:
                        logger.error(f"Failed to fetch health update: {e}")
                        await websocket.send_json({
                            "type": "error",
                            "message": "Failed to fetch health update",
                        })

                elif message.get("type") == "subscribe_alerts":
                    # Subscribe to alerts (alerts are sent automatically when detected)
                    await websocket.send_json({
                        "type": "subscription_confirmed",
                        "subscription": "alerts",
                        "timestamp": datetime.utcnow().isoformat(),
                    })

                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")

            except json.JSONDecodeError:
                logger.error("Failed to parse WebSocket message as JSON")
                await websocket.send_json({
                    "type": "error",
                    "message": "Invalid JSON format",
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"User {user_id} disconnected from health monitoring WebSocket")

    except Exception as e:
        logger.error(f"WebSocket error for user {user_id}: {e}")
        manager.disconnect(websocket, user_id)


# Helper function to send alerts to specific users (can be called from other parts of the app)
async def send_health_alert(user_id: str, alert_data: dict):
    """
    Send a health alert to a specific user

    This can be called from background tasks or other endpoints
    to push real-time alerts to connected clients.

    Args:
        user_id: The user ID to send the alert to
        alert_data: Dictionary containing alert information
            - alert_type: Type of alert (stress_spike, burnout_detected, etc.)
            - severity: Alert severity (critical, high, medium, low)
            - message: Alert message
    """
    await manager.send_personal_message({
        "type": "health_alert",
        "data": {
            "id": f"alert_{datetime.utcnow().timestamp()}",
            "user_id": user_id,
            "timestamp": datetime.utcnow().isoformat(),
            **alert_data
        }
    }, user_id)


# Helper function to broadcast organizational updates
async def broadcast_health_update(update_data: dict):
    """
    Broadcast a health update to all connected users

    This can be used for organization-wide health notifications
    or system-wide announcements.

    Args:
        update_data: Dictionary containing update information
    """
    await manager.broadcast({
        "type": "health_update",
        "data": {
            "timestamp": datetime.utcnow().isoformat(),
            **update_data
        }
    })


# Export the router and helper functions
__all__ = [
    "ws_router",
    "send_health_alert",
    "broadcast_health_update",
    "manager",
]
