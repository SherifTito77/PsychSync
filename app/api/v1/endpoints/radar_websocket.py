"""
Real-time WebSocket Monitoring for Radar System
Provides live updates for zone changes, patterns, and alerts
"""

import json
import logging
from datetime import datetime
from typing import Dict, Set
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db
from app.db.models.user import User
from app.services.radar_realtime_processor import realtime_signal_processor

logger = logging.getLogger(__name__)


class RadarWebSocketManager:
    """
    WebSocket connection manager for real-time radar updates

    Features:
    - Organization-based room management
    - Selective broadcasting (by org, team, or user)
    - Connection health monitoring
    - Automatic reconnection support
    - Per-IP connection limits (prevents DoS attacks)
    """

    # Maximum connections per IP address
    MAX_CONNECTIONS_PER_IP = 5

    def __init__(self):
        # Track active connections: room_id -> set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Track which rooms each connection is subscribed to
        self.connection_rooms: Dict[WebSocket, Set[str]] = {}

        # Track metadata for each connection
        self.connection_metadata: Dict[WebSocket, Dict] = {}

        # Track connections per IP address
        self.ip_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, organization_id: str, user_id: str):
        """Connect a new WebSocket client with IP-based rate limiting"""
        # Get client IP address
        client_ip = websocket.client.host if websocket.client else "unknown"

        # Check IP connection limit BEFORE accepting
        if client_ip in self.ip_connections:
            ip_connections = self.ip_connections[client_ip]
            if len(ip_connections) >= self.MAX_CONNECTIONS_PER_IP:
                # Reject connection if IP has too many active connections
                logger.warning(
                    f"WebSocket connection rejected: IP {client_ip} has "
                    f"{len(ip_connections)} active connections (max: {self.MAX_CONNECTIONS_PER_IP})"
                )
                await websocket.close(
                    code=1008,
                    reason=f"Too many connections from your IP. Maximum is {self.MAX_CONNECTIONS_PER_IP}.",
                )
                return False  # Connection rejected

        # Generate connection ID
        connection_id = str(uuid4())

        # Accept the connection
        await websocket.accept()

        # Store metadata
        self.connection_metadata[websocket] = {
            "connection_id": connection_id,
            "organization_id": organization_id,
            "user_id": user_id,
            "connected_at": datetime.utcnow().isoformat(),
            "client_ip": client_ip,
        }

        # Track IP-based connections
        if client_ip not in self.ip_connections:
            self.ip_connections[client_ip] = set()
        self.ip_connections[client_ip].add(websocket)

        # Auto-subscribe to organization room
        org_room = f"org:{organization_id}"
        await self.subscribe(websocket, org_room)

        # Send welcome message
        await self.send_personal_message(
            {
                "type": "connected",
                "connection_id": connection_id,
                "message": "Connected to Radar WebSocket",
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        logger.info(
            f"WebSocket connected: {connection_id} for org {organization_id} from IP {client_ip}"
        )
        return True  # Connection accepted

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket client with IP cleanup"""
        # Get IP before cleanup
        client_ip = self.connection_metadata.get(websocket, {}).get(
            "client_ip", "unknown"
        )

        # Unsubscribe from all rooms
        if websocket in self.connection_rooms:
            for room in self.connection_rooms[websocket]:
                await self.unsubscribe(websocket, room)

        # Clean up IP-based connection tracking
        if client_ip and client_ip in self.ip_connections:
            if websocket in self.ip_connections[client_ip]:
                self.ip_connections[client_ip].discard(websocket)

        # Clean up metadata
        if websocket in self.connection_metadata:
            connection_id = self.connection_metadata[websocket]["connection_id"]
            logger.info(f"WebSocket disconnected: {connection_id} from IP {client_ip}")
            del self.connection_metadata[websocket]

    async def subscribe(self, websocket: WebSocket, room: str):
        """Subscribe a connection to a room"""
        if room not in self.active_connections:
            self.active_connections[room] = set()

        self.active_connections[room].add(websocket)

        if websocket not in self.connection_rooms:
            self.connection_rooms[websocket] = set()

        self.connection_rooms[websocket].add(room)

        await self.send_personal_message(
            {
                "type": "subscribed",
                "room": room,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

        logger.debug(
            f"Connection {self.connection_metadata.get(websocket, {}).get('connection_id')} subscribed to {room}"
        )

    async def unsubscribe(self, websocket: WebSocket, room: str):
        """Unsubscribe a connection from a room"""
        if room in self.active_connections:
            self.active_connections[room].discard(websocket)

        if websocket in self.connection_rooms:
            self.connection_rooms[websocket].discard(room)

        await self.send_personal_message(
            {
                "type": "unsubscribed",
                "room": room,
                "timestamp": datetime.utcnow().isoformat(),
            },
            websocket,
        )

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_text(json.dumps(message))
        except Exception as e:
            logger.error(f"Failed to send message to websocket: {e}")
            await self.disconnect(websocket)

    async def broadcast_to_room(self, message: dict, room: str):
        """Broadcast a message to all connections in a room"""
        if room not in self.active_connections:
            return

        # Store message with timestamp
        message["timestamp"] = datetime.utcnow().isoformat()

        # Send to all connections in room
        disconnected = set()
        for connection in self.active_connections[room]:
            try:
                await connection.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)

        # Clean up disconnected connections
        for connection in disconnected:
            await self.disconnect(connection)

    async def broadcast_zone_update(
        self, organization_id: str, zone: str, risk_score: float, confidence: float
    ):
        """Broadcast zone classification update"""
        room = f"org:{organization_id}"
        message = {
            "type": "zone_update",
            "data": {
                "zone": zone,
                "risk_score": risk_score,
                "confidence": confidence,
            },
        }
        await self.broadcast_to_room(message, room)

    async def broadcast_pattern_detected(self, organization_id: str, pattern: dict):
        """Broadcast new pattern detection"""
        room = f"org:{organization_id}"
        message = {"type": "pattern_detected", "data": pattern}
        await self.broadcast_to_room(message, room)

    async def broadcast_alert(self, organization_id: str, alert: dict):
        """Broadcast critical alert"""
        room = f"org:{organization_id}"
        message = {"type": "alert", "data": alert}
        await self.broadcast_to_room(message, room)

    async def broadcast_signal_processed(self, organization_id: str, signal_data: dict):
        """Broadcast signal processing result"""
        room = f"org:{organization_id}"
        message = {"type": "signal_processed", "data": signal_data}
        await self.broadcast_to_room(message, room)

    def get_connection_stats(self) -> dict:
        """Get statistics about active connections including IP-based tracking"""
        total_connections = sum(
            len(conns) for conns in self.active_connections.values()
        )

        room_stats = {}
        for room, connections in self.active_connections.items():
            room_stats[room] = len(connections)

        # IP-based connection stats
        ip_stats = {}
        for ip, conns in self.ip_connections.items():
            ip_stats[ip] = {
                "connections": len(conns),
                "max_allowed": self.MAX_CONNECTIONS_PER_IP,
            }

        return {
            "total_connections": total_connections,
            "active_rooms": len(self.active_connections),
            "room_stats": room_stats,
            "ip_connections": ip_stats,
        }


# Global WebSocket manager instance
radar_websocket_manager = RadarWebSocketManager()
