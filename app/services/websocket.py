"""
WebSocket service for real-time chat.
Handles connections, message routing, and online status.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Set
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import verify_token_type
from app.core.redis import RedisClient, CacheKeys
from app.models.user import User
from app.models.chat import Dialog, Message


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    user_id: int
    user_name: str
    connected_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ConnectionManager:
    """
    Manages WebSocket connections for real-time chat.
    
    Features:
    - Tracks active connections by user_id
    - Handles message broadcasting
    - Manages online status
    - Supports multiple connections per user (multiple devices)
    """

    def __init__(self):
        # user_id -> list of connections (supports multiple devices)
        self.active_connections: Dict[int, list[ConnectionInfo]] = {}
        # dialog_id -> set of user_ids subscribed to this dialog
        self.dialog_subscribers: Dict[int, Set[int]] = {}
        self._lock = asyncio.Lock()

    async def connect(
        self,
        websocket: WebSocket,
        user_id: int,
        user_name: str,
    ) -> ConnectionInfo:
        """
        Accept a new WebSocket connection.
        """
        await websocket.accept()
        
        connection = ConnectionInfo(
            websocket=websocket,
            user_id=user_id,
            user_name=user_name,
        )

        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(connection)

        # Update online status in Redis
        await self._set_online_status(user_id, True)

        # Notify contacts about online status
        await self._broadcast_online_status(user_id, True)

        return connection

    async def disconnect(self, connection: ConnectionInfo):
        """
        Handle WebSocket disconnection.
        """
        user_id = connection.user_id

        async with self._lock:
            if user_id in self.active_connections:
                self.active_connections[user_id] = [
                    c for c in self.active_connections[user_id]
                    if c.websocket != connection.websocket
                ]
                if not self.active_connections[user_id]:
                    del self.active_connections[user_id]
                    # Only mark offline if no connections left
                    await self._set_online_status(user_id, False)
                    await self._broadcast_online_status(user_id, False)

            # Remove from dialog subscribers
            for dialog_id, subscribers in list(self.dialog_subscribers.items()):
                subscribers.discard(user_id)
                if not subscribers:
                    del self.dialog_subscribers[dialog_id]

    async def subscribe_to_dialog(self, user_id: int, dialog_id: int):
        """
        Subscribe user to receive messages from a dialog.
        """
        async with self._lock:
            if dialog_id not in self.dialog_subscribers:
                self.dialog_subscribers[dialog_id] = set()
            self.dialog_subscribers[dialog_id].add(user_id)

    async def unsubscribe_from_dialog(self, user_id: int, dialog_id: int):
        """
        Unsubscribe user from a dialog.
        """
        async with self._lock:
            if dialog_id in self.dialog_subscribers:
                self.dialog_subscribers[dialog_id].discard(user_id)

    async def send_personal_message(self, user_id: int, message: dict):
        """
        Send message to all connections of a specific user.
        """
        if user_id in self.active_connections:
            message_text = json.dumps(message)
            for connection in self.active_connections[user_id]:
                try:
                    await connection.websocket.send_text(message_text)
                except Exception:
                    # Connection might be closed
                    pass

    async def broadcast_to_dialog(self, dialog_id: int, message: dict, exclude_user: Optional[int] = None):
        """
        Broadcast message to all users subscribed to a dialog.
        """
        if dialog_id not in self.dialog_subscribers:
            return

        for user_id in self.dialog_subscribers[dialog_id]:
            if user_id != exclude_user:
                await self.send_personal_message(user_id, message)

    async def send_new_message(
        self,
        dialog_id: int,
        message: dict,
        recipient_id: int,
    ):
        """
        Send new message notification to recipient.
        """
        await self.send_personal_message(recipient_id, {
            "type": "new_message",
            "dialog_id": dialog_id,
            "message": message,
        })

    async def send_message_read(
        self,
        dialog_id: int,
        message_id: int,
        reader_id: int,
        sender_id: int,
    ):
        """
        Notify sender that message was read.
        """
        await self.send_personal_message(sender_id, {
            "type": "message_read",
            "dialog_id": dialog_id,
            "message_id": message_id,
            "reader_id": reader_id,
            "read_at": datetime.now(timezone.utc).isoformat(),
        })

    async def send_typing_indicator(
        self,
        dialog_id: int,
        user_id: int,
        is_typing: bool,
        recipient_id: int,
    ):
        """
        Send typing indicator to recipient.
        """
        await self.send_personal_message(recipient_id, {
            "type": "typing",
            "dialog_id": dialog_id,
            "user_id": user_id,
            "is_typing": is_typing,
        })

    def is_user_online(self, user_id: int) -> bool:
        """
        Check if user has any active connections.
        """
        return user_id in self.active_connections and len(self.active_connections[user_id]) > 0

    def get_online_users(self) -> list[int]:
        """
        Get list of all online user IDs.
        """
        return list(self.active_connections.keys())

    async def _set_online_status(self, user_id: int, is_online: bool):
        """
        Store online status in Redis.
        """
        try:
            client = await RedisClient.get_client()
            key = f"{CacheKeys.ONLINE_USERS}{user_id}"
            if is_online:
                await client.set(key, "1", ex=300)  # 5 min TTL, refreshed periodically
            else:
                await client.delete(key)
                # Store last seen
                await client.set(f"{key}:last_seen", datetime.now(timezone.utc).isoformat())
        except Exception:
            # Redis might not be available
            pass

    async def _broadcast_online_status(self, user_id: int, is_online: bool):
        """
        Broadcast online status change to user's contacts.
        """
        # This would notify all users who have dialogs with this user
        # For simplicity, we skip this in the initial implementation
        pass


# Global connection manager instance
manager = ConnectionManager()


async def authenticate_websocket(websocket: WebSocket, db: AsyncSession) -> Optional[User]:
    """
    Authenticate WebSocket connection using access token from query params or headers.
    """
    # Try to get token from query params
    token = websocket.query_params.get("token")

    # Or from cookies
    if not token:
        cookies = websocket.cookies
        token = cookies.get("access_token")

    if not token:
        return None

    # Verify token
    payload = verify_token_type(token, "access")
    if not payload:
        return None

    user_id = payload.get("sub")
    if not user_id:
        return None

    # Get user
    result = await db.execute(
        select(User).where(User.id == int(user_id), User.deleted_at.is_(None))
    )
    user = result.scalar_one_or_none()

    if user and user.is_active and not user.is_blocked:
        return user

    return None


async def handle_websocket_message(
    connection: ConnectionInfo,
    data: dict,
    db: AsyncSession,
):
    """
    Handle incoming WebSocket message.
    """
    message_type = data.get("type")

    if message_type == "ping":
        # Heartbeat
        await connection.websocket.send_json({"type": "pong"})

    elif message_type == "subscribe":
        # Subscribe to a dialog
        dialog_id = data.get("dialog_id")
        if dialog_id:
            # Verify user is participant
            result = await db.execute(
                select(Dialog).where(Dialog.id == dialog_id)
            )
            dialog = result.scalar_one_or_none()
            if dialog and dialog.is_participant(connection.user_id):
                await manager.subscribe_to_dialog(connection.user_id, dialog_id)
                await connection.websocket.send_json({
                    "type": "subscribed",
                    "dialog_id": dialog_id,
                })

    elif message_type == "unsubscribe":
        # Unsubscribe from a dialog
        dialog_id = data.get("dialog_id")
        if dialog_id:
            await manager.unsubscribe_from_dialog(connection.user_id, dialog_id)

    elif message_type == "typing":
        # Typing indicator
        dialog_id = data.get("dialog_id")
        is_typing = data.get("is_typing", False)

        if dialog_id:
            result = await db.execute(
                select(Dialog).where(Dialog.id == dialog_id)
            )
            dialog = result.scalar_one_or_none()
            if dialog and dialog.is_participant(connection.user_id):
                recipient_id = dialog.get_other_user_id(connection.user_id)
                await manager.send_typing_indicator(
                    dialog_id,
                    connection.user_id,
                    is_typing,
                    recipient_id,
                )

    elif message_type == "message":
        # New message (can also be handled via REST API)
        dialog_id = data.get("dialog_id")
        text = data.get("text")

        if dialog_id and text:
            result = await db.execute(
                select(Dialog).where(Dialog.id == dialog_id)
            )
            dialog = result.scalar_one_or_none()

            if dialog and dialog.is_participant(connection.user_id):
                if dialog.is_blocked():
                    await connection.websocket.send_json({
                        "type": "error",
                        "message": "Cannot send messages in blocked dialog",
                    })
                    return

                # Create message
                message = Message(
                    dialog_id=dialog_id,
                    sender_id=connection.user_id,
                    text=text,
                )
                db.add(message)

                # Update dialog
                dialog.last_message_id = message.id
                dialog.last_message_at = message.created_at
                dialog.last_message_text = text[:255]

                recipient_id = dialog.get_other_user_id(connection.user_id)
                dialog.increment_unread_count(recipient_id)

                await db.commit()
                await db.refresh(message)

                # Notify sender
                await connection.websocket.send_json({
                    "type": "message_sent",
                    "message_id": message.id,
                    "dialog_id": dialog_id,
                    "created_at": message.created_at.isoformat(),
                })

                # Notify recipient
                await manager.send_new_message(
                    dialog_id,
                    {
                        "id": message.id,
                        "sender_id": connection.user_id,
                        "text": text,
                        "created_at": message.created_at.isoformat(),
                    },
                    recipient_id,
                )

    elif message_type == "mark_read":
        # Mark messages as read
        dialog_id = data.get("dialog_id")
        message_ids = data.get("message_ids", [])

        if dialog_id and message_ids:
            result = await db.execute(
                select(Dialog).where(Dialog.id == dialog_id)
            )
            dialog = result.scalar_one_or_none()

            if dialog and dialog.is_participant(connection.user_id):
                for msg_id in message_ids:
                    result = await db.execute(
                        select(Message).where(
                            Message.id == msg_id,
                            Message.dialog_id == dialog_id,
                            Message.sender_id != connection.user_id,
                        )
                    )
                    message = result.scalar_one_or_none()
                    if message and not message.is_read:
                        message.mark_as_read()
                        # Notify sender
                        await manager.send_message_read(
                            dialog_id,
                            msg_id,
                            connection.user_id,
                            message.sender_id,
                        )

                dialog.reset_unread_count(connection.user_id)
                await db.commit()

