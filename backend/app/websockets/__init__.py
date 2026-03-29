"""
WebSocket infrastructure for real-time notifications.
"""
from app.websockets.connection_manager import WebSocketConnectionManager, websocket_manager

__all__ = ["WebSocketConnectionManager", "websocket_manager"]