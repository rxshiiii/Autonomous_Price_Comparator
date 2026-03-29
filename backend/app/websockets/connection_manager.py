"""
WebSocket connection management for real-time notifications.
"""
from typing import Dict, List, Set
from uuid import UUID
from fastapi import WebSocket
from collections import defaultdict
import json
from datetime import datetime
import structlog


logger = structlog.get_logger()


class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time notifications."""

    def __init__(self):
        """Initialize connection manager."""
        # Store multiple connections per user (mobile + desktop)
        self.active_connections: Dict[UUID, List[WebSocket]] = defaultdict(list)
        # Map connection to user for cleanup
        self.connection_to_user: Dict[WebSocket, UUID] = {}
        # Track connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
        self.logger = logger.bind(service="websocket_manager")

    async def connect(self, websocket: WebSocket, user_id: UUID, metadata: Dict = None) -> bool:
        """
        Connect a new WebSocket for a user.

        Args:
            websocket: WebSocket connection instance
            user_id: User UUID
            metadata: Connection metadata (device info, etc.)

        Returns:
            True if connected successfully
        """
        try:
            await websocket.accept()

            # Store connection
            self.active_connections[user_id].append(websocket)
            self.connection_to_user[websocket] = user_id
            self.connection_metadata[websocket] = metadata or {}

            self.logger.info(
                "websocket_connected",
                user_id=str(user_id),
                connections_count=len(self.active_connections[user_id]),
                total_users=len(self.active_connections)
            )

            # Send welcome message
            await self.send_personal_message({
                "type": "system",
                "message": "Connected successfully",
                "timestamp": datetime.utcnow().isoformat()
            }, user_id)

            return True

        except Exception as e:
            self.logger.error("websocket_connection_failed", error=str(e), user_id=str(user_id))
            return False

    async def disconnect(self, websocket: WebSocket):
        """
        Disconnect a WebSocket and clean up.

        Args:
            websocket: WebSocket connection to disconnect
        """
        try:
            user_id = self.connection_to_user.get(websocket)
            if user_id:
                # Remove from active connections
                if websocket in self.active_connections[user_id]:
                    self.active_connections[user_id].remove(websocket)

                # Clean up empty user entries
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]

                # Clean up metadata
                self.connection_to_user.pop(websocket, None)
                self.connection_metadata.pop(websocket, None)

                self.logger.info(
                    "websocket_disconnected",
                    user_id=str(user_id),
                    remaining_connections=len(self.active_connections.get(user_id, [])),
                    total_users=len(self.active_connections)
                )

        except Exception as e:
            self.logger.error("websocket_disconnect_failed", error=str(e))

    async def send_personal_message(self, message: Dict, user_id: UUID) -> bool:
        """
        Send a message to a specific user across all their connections.

        Args:
            message: Message dictionary to send
            user_id: Target user UUID

        Returns:
            True if sent to at least one connection
        """
        if user_id not in self.active_connections:
            self.logger.warning("no_active_connections", user_id=str(user_id))
            return False

        connections = self.active_connections[user_id].copy()
        successful_sends = 0
        failed_connections = []

        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
                successful_sends += 1

            except Exception as e:
                self.logger.warning("websocket_send_failed", error=str(e), user_id=str(user_id))
                failed_connections.append(websocket)

        # Clean up failed connections
        for failed_ws in failed_connections:
            await self.disconnect(failed_ws)

        self.logger.info(
            "message_sent",
            user_id=str(user_id),
            successful_sends=successful_sends,
            failed_sends=len(failed_connections),
            message_type=message.get("type", "unknown")
        )

        return successful_sends > 0

    async def broadcast_to_users(self, message: Dict, user_ids: List[UUID]) -> int:
        """
        Broadcast message to multiple users.

        Args:
            message: Message dictionary to broadcast
            user_ids: List of user UUIDs to send to

        Returns:
            Number of users successfully reached
        """
        successful_users = 0

        for user_id in user_ids:
            if await self.send_personal_message(message, user_id):
                successful_users += 1

        self.logger.info(
            "broadcast_completed",
            target_users=len(user_ids),
            successful_users=successful_users,
            message_type=message.get("type", "unknown")
        )

        return successful_users

    async def send_notification(self, notification_data: Dict, user_id: UUID) -> bool:
        """
        Send a formatted notification message to a user.

        Args:
            notification_data: Notification data from database
            user_id: Target user UUID

        Returns:
            True if sent successfully
        """
        message = {
            "type": "notification",
            "subtype": notification_data.get("notification_type", "general"),
            "data": {
                "notification_id": notification_data.get("id"),
                "title": notification_data.get("title"),
                "message": notification_data.get("message"),
                "timestamp": notification_data.get("created_at", datetime.utcnow()).isoformat(),
                "data": notification_data.get("data", {}),
                "is_read": notification_data.get("is_read", False)
            }
        }

        return await self.send_personal_message(message, user_id)

    def get_user_connection_count(self, user_id: UUID) -> int:
        """Get number of active connections for a user."""
        return len(self.active_connections.get(user_id, []))

    def get_total_connections(self) -> int:
        """Get total number of active connections."""
        return sum(len(connections) for connections in self.active_connections.values())

    def get_connected_users(self) -> Set[UUID]:
        """Get set of all connected user IDs."""
        return set(self.active_connections.keys())

    async def ping_all_connections(self):
        """Send ping to all connections to check health."""
        ping_message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }

        failed_connections = []
        total_connections = 0

        for user_id, connections in self.active_connections.items():
            for websocket in connections:
                total_connections += 1
                try:
                    await websocket.send_text(json.dumps(ping_message))
                except Exception:
                    failed_connections.append(websocket)

        # Clean up failed connections
        for failed_ws in failed_connections:
            await self.disconnect(failed_ws)

        self.logger.info(
            "ping_completed",
            total_connections=total_connections,
            failed_connections=len(failed_connections),
            healthy_connections=total_connections - len(failed_connections)
        )


# Global connection manager instance
websocket_manager = WebSocketConnectionManager()