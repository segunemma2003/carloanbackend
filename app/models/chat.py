"""
Chat/Messaging models.
WebSocket-based real-time messaging between users.
"""

from datetime import datetime, timezone
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ad import Ad


class Dialog(Base, TimestampMixin):
    """
    Chat dialog between two users about an ad.
    Each dialog is linked to a specific ad and has exactly two participants.
    """

    __tablename__ = "dialogs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Related ad
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Participants
    seller_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Last message info (cached for list display)
    last_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_message_text: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Unread counters
    seller_unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    buyer_unread_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Dialog state
    is_seller_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_buyer_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Blocking
    seller_blocked_buyer: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    buyer_blocked_seller: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad", back_populates="dialogs")
    seller: Mapped["User"] = relationship(
        "User",
        foreign_keys=[seller_id],
    )
    buyer: Mapped["User"] = relationship(
        "User",
        foreign_keys=[buyer_id],
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="dialog",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:
        return f"<Dialog(id={self.id}, ad_id={self.ad_id}, seller_id={self.seller_id}, buyer_id={self.buyer_id})>"

    def get_other_user_id(self, user_id: int) -> int:
        """Get the ID of the other participant."""
        return self.buyer_id if user_id == self.seller_id else self.seller_id

    def is_participant(self, user_id: int) -> bool:
        """Check if user is a participant in this dialog."""
        return user_id in (self.seller_id, self.buyer_id)

    def is_blocked(self) -> bool:
        """Check if dialog is blocked by either party."""
        return self.seller_blocked_buyer or self.buyer_blocked_seller

    def get_unread_count(self, user_id: int) -> int:
        """Get unread count for a specific user."""
        if user_id == self.seller_id:
            return self.seller_unread_count
        return self.buyer_unread_count

    def reset_unread_count(self, user_id: int) -> None:
        """Reset unread count for a specific user."""
        if user_id == self.seller_id:
            self.seller_unread_count = 0
        else:
            self.buyer_unread_count = 0

    def increment_unread_count(self, for_user_id: int) -> None:
        """Increment unread count for a specific user."""
        if for_user_id == self.seller_id:
            self.seller_unread_count += 1
        else:
            self.buyer_unread_count += 1


class Message(Base, TimestampMixin):
    """Individual chat message."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    dialog_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("dialogs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sender_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Message content
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Attachments (JSON array of attachment objects)
    attachments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Message status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Delivery status
    is_delivered: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Soft delete for individual users
    is_deleted_by_sender: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_deleted_by_recipient: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # System messages
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    system_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    dialog: Mapped["Dialog"] = relationship("Dialog", back_populates="messages")
    sender: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Message(id={self.id}, dialog_id={self.dialog_id}, sender_id={self.sender_id})>"

    def mark_as_read(self) -> None:
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.now(timezone.utc)

    def mark_as_delivered(self) -> None:
        """Mark message as delivered."""
        if not self.is_delivered:
            self.is_delivered = True
            self.delivered_at = datetime.now(timezone.utc)


class MessageAttachment(Base, TimestampMixin):
    """Attachment for chat messages (images, files)."""

    __tablename__ = "message_attachments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    file_type: Mapped[str] = mapped_column(String(50), nullable=False)  # image, document
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    def __repr__(self) -> str:
        return f"<MessageAttachment(id={self.id}, message_id={self.message_id})>"

