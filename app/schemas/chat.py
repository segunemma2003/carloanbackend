"""
Chat/Messaging schemas.
"""

from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field

from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse


class MessageCreate(BaseModel):
    """Create message schema."""

    text: Optional[str] = Field(None, max_length=5000)
    attachments: Optional[List[dict]] = None


class MessageResponse(BaseSchema):
    """Message response."""

    id: int
    dialog_id: int
    sender_id: int
    sender: UserResponse
    text: Optional[str] = None
    attachments: Optional[List[dict]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    is_delivered: bool
    delivered_at: Optional[datetime] = None
    is_system: bool
    system_type: Optional[str] = None
    created_at: datetime


class MessageUpdate(BaseModel):
    """Update message (mark as read/delivered)."""

    is_read: Optional[bool] = None


class DialogResponse(BaseSchema):
    """Dialog response."""

    id: int
    ad_id: int
    ad_title: str
    ad_main_image: Optional[str] = None
    ad_price: str
    
    seller_id: int
    buyer_id: int
    other_user: UserResponse  # The other participant
    
    last_message_text: Optional[str] = None
    last_message_at: Optional[datetime] = None
    unread_count: int
    
    is_blocked: bool
    created_at: datetime


class DialogListResponse(BaseModel):
    """List of dialogs."""

    dialogs: List[DialogResponse]
    total: int
    unread_total: int


class DialogDetail(DialogResponse):
    """Dialog with messages."""

    messages: List[MessageResponse] = []


class DialogCreate(BaseModel):
    """Create dialog (start conversation)."""

    ad_id: int
    initial_message: Optional[str] = Field(None, max_length=5000)


class TypingIndicator(BaseModel):
    """Typing indicator for WebSocket."""

    dialog_id: int
    user_id: int
    is_typing: bool


class OnlineStatus(BaseModel):
    """User online status."""

    user_id: int
    is_online: bool
    last_seen_at: Optional[datetime] = None


# WebSocket message types
class WSMessage(BaseModel):
    """Base WebSocket message."""

    type: str
    data: dict


class WSNewMessage(BaseModel):
    """New message via WebSocket."""

    type: str = "new_message"
    message: MessageResponse


class WSMessageRead(BaseModel):
    """Message read notification via WebSocket."""

    type: str = "message_read"
    dialog_id: int
    message_id: int
    read_at: datetime


class WSTyping(BaseModel):
    """Typing indicator via WebSocket."""

    type: str = "typing"
    dialog_id: int
    user_id: int
    is_typing: bool


class WSOnlineStatus(BaseModel):
    """Online status via WebSocket."""

    type: str = "online_status"
    user_id: int
    is_online: bool


class ChatBlock(BaseModel):
    """Block/unblock user in chat."""

    user_id: int
    block: bool


class ChatReport(BaseModel):
    """Report chat/user."""

    dialog_id: int
    reason: str
    description: Optional[str] = None

