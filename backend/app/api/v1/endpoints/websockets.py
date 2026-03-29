"""
WebSocket endpoints for real-time notifications.
"""
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import json
import structlog

from app.db.session import get_db
from app.core.security import decode_token
from app.models.user import User
from app.websockets.connection_manager import websocket_manager
from app.models.notification import Notification


logger = structlog.get_logger()
router = APIRouter()


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    """
    Authenticate user from JWT token for WebSocket connection.

    Args:
        token: JWT token string
        db: Database session

    Returns:
        User object if valid, None if invalid
    """
    try:
        # Decode JWT token
        payload = decode_token(token)
        if payload is None:
            return None

        # Check token type
        if payload.get("type") != "access":
            return None

        user_id = payload.get("sub")
        if user_id is None:
            return None

        # Get user from database
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None or not user.is_active:
            return None

        return user

    except Exception as e:
        logger.error("websocket_auth_failed", error=str(e))
        return None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT authentication token"),
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications.

    Args:
        websocket: WebSocket connection
        token: JWT token for authentication
        db: Database session

    Protocol:
        - Client connects with JWT token as query parameter
        - Server validates token and user
        - Connection established for real-time notifications
        - Server sends notifications as JSON messages
        - Client can send control messages (mark as read, etc.)
    """
    user = await get_user_from_token(token, db)
    if not user:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Get connection metadata
    client_info = {
        "user_agent": websocket.headers.get("user-agent", "unknown"),
        "connected_at": str(websocket.client),
        "connection_time": None
    }

    # Connect to manager
    connected = await websocket_manager.connect(websocket, user.id, client_info)
    if not connected:
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    try:
        # Send initial data (unread count, recent notifications)
        await send_initial_data(websocket, user.id, db)

        # Listen for client messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)

                # Handle different message types
                await handle_client_message(websocket, user.id, message, db)

            except WebSocketDisconnect:
                logger.info("websocket_client_disconnected", user_id=str(user.id))
                break

            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Invalid JSON format"
                }))

            except Exception as e:
                logger.error("websocket_message_handling_error", error=str(e), user_id=str(user.id))
                await websocket.send_text(json.dumps({
                    "type": "error",
                    "message": "Message processing error"
                }))

    except WebSocketDisconnect:
        logger.info("websocket_disconnected", user_id=str(user.id))
    except Exception as e:
        logger.error("websocket_error", error=str(e), user_id=str(user.id))
    finally:
        await websocket_manager.disconnect(websocket)


async def send_initial_data(websocket: WebSocket, user_id: str, db: AsyncSession):
    """
    Send initial data to newly connected client.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        db: Database session
    """
    try:
        # Get unread notification count
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .order_by(Notification.created_at.desc())
            .limit(10)
        )
        recent_notifications = result.scalars().all()

        # Get unread count
        unread_count = len([n for n in recent_notifications if not n.is_read])

        # Format notifications for client
        formatted_notifications = []
        for notif in recent_notifications:
            formatted_notifications.append({
                "id": str(notif.id),
                "type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "data": notif.data,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat(),
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None
            })

        # Send initial data
        initial_message = {
            "type": "initial_data",
            "data": {
                "unread_count": unread_count,
                "recent_notifications": formatted_notifications,
                "connection_status": "connected"
            }
        }

        await websocket.send_text(json.dumps(initial_message))
        logger.info("initial_data_sent", user_id=user_id, unread_count=unread_count)

    except Exception as e:
        logger.error("send_initial_data_failed", error=str(e), user_id=user_id)


async def handle_client_message(websocket: WebSocket, user_id: str, message: dict, db: AsyncSession):
    """
    Handle messages received from WebSocket client.

    Args:
        websocket: WebSocket connection
        user_id: User ID
        message: Parsed message from client
        db: Database session
    """
    message_type = message.get("type")

    if message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({
            "type": "pong",
            "timestamp": message.get("timestamp")
        }))

    elif message_type == "mark_as_read":
        # Mark notification as read
        notification_id = message.get("notification_id")
        if notification_id:
            await mark_notification_as_read(notification_id, user_id, db)
            await websocket.send_text(json.dumps({
                "type": "marked_as_read",
                "notification_id": notification_id
            }))

    elif message_type == "mark_all_read":
        # Mark all notifications as read
        await mark_all_notifications_as_read(user_id, db)
        await websocket.send_text(json.dumps({
            "type": "all_marked_as_read"
        }))

    elif message_type == "get_recent":
        # Get recent notifications
        limit = message.get("limit", 20)
        await send_recent_notifications(websocket, user_id, limit, db)

    else:
        logger.warning("unknown_message_type", message_type=message_type, user_id=user_id)


async def mark_notification_as_read(notification_id: str, user_id: str, db: AsyncSession):
    """Mark a notification as read."""
    try:
        result = await db.execute(
            select(Notification).where(
                Notification.id == notification_id,
                Notification.user_id == user_id
            )
        )
        notification = result.scalar_one_or_none()

        if notification:
            notification.is_read = True
            await db.commit()
            logger.info("notification_marked_read", notification_id=notification_id, user_id=user_id)

    except Exception as e:
        logger.error("mark_notification_read_failed", error=str(e))
        await db.rollback()


async def mark_all_notifications_as_read(user_id: str, db: AsyncSession):
    """Mark all notifications as read for a user."""
    try:
        result = await db.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read == False
            )
        )
        notifications = result.scalars().all()

        for notification in notifications:
            notification.is_read = True

        await db.commit()
        logger.info("all_notifications_marked_read", user_id=user_id, count=len(notifications))

    except Exception as e:
        logger.error("mark_all_notifications_read_failed", error=str(e))
        await db.rollback()


async def send_recent_notifications(websocket: WebSocket, user_id: str, limit: int, db: AsyncSession):
    """Send recent notifications to client."""
    try:
        result = await db.execute(
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        notifications = result.scalars().all()

        formatted_notifications = []
        for notif in notifications:
            formatted_notifications.append({
                "id": str(notif.id),
                "type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "data": notif.data,
                "is_read": notif.is_read,
                "created_at": notif.created_at.isoformat(),
                "sent_at": notif.sent_at.isoformat() if notif.sent_at else None
            })

        await websocket.send_text(json.dumps({
            "type": "recent_notifications",
            "data": {
                "notifications": formatted_notifications,
                "count": len(formatted_notifications)
            }
        }))

    except Exception as e:
        logger.error("send_recent_notifications_failed", error=str(e))


# Test endpoint for manual WebSocket message sending
@router.post("/test-message")
async def send_test_message(
    user_id: str,
    message: str
):
    """
    Test endpoint to send a WebSocket message to a specific user.
    Only for testing purposes.
    """
    from datetime import datetime

    test_message = {
        "type": "test",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    success = await websocket_manager.send_personal_message(test_message, user_id)
    return {"sent": success, "user_id": user_id}