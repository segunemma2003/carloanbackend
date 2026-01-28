"""
Moderation and reporting models.
"""

import enum
from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
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


class ReportType(str, enum.Enum):
    """Type of content being reported."""
    AD = "ad"
    USER = "user"
    MESSAGE = "message"


class ReportReason(str, enum.Enum):
    """Reason for the report."""
    FRAUD = "fraud"
    SPAM = "spam"
    INAPPROPRIATE = "inappropriate"
    WRONG_CATEGORY = "wrong_category"
    WRONG_PRICE = "wrong_price"
    DUPLICATE = "duplicate"
    SOLD = "sold"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    """Report status."""
    PENDING = "pending"
    REVIEWING = "reviewing"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class ModerationAction(str, enum.Enum):
    """Types of moderation actions."""
    APPROVE = "approve"
    REJECT = "reject"
    BLOCK_USER = "block_user"
    UNBLOCK_USER = "unblock_user"
    BLOCK_AD = "block_ad"
    UNBLOCK_AD = "unblock_ad"
    DELETE_AD = "delete_ad"
    DELETE_MESSAGE = "delete_message"
    WARNING = "warning"


class Report(Base, TimestampMixin):
    """User reports on ads, users, or messages."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Reporter
    reporter_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,  # Allow anonymous reports
        index=True,
    )
    
    # Report target
    report_type: Mapped[ReportType] = mapped_column(
        Enum(ReportType),
        nullable=False,
    )
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Report details
    reason: Mapped[ReportReason] = mapped_column(
        Enum(ReportReason),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus),
        default=ReportStatus.PENDING,
        nullable=False,
        index=True,
    )
    
    # Resolution
    resolved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolution_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    reporter: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[reporter_id],
    )
    resolver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[resolved_by],
    )

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, type={self.report_type}, target_id={self.target_id})>"

    def resolve(
        self,
        moderator_id: int,
        status: ReportStatus,
        note: Optional[str] = None,
    ) -> None:
        """Resolve the report."""
        self.status = status
        self.resolved_by = moderator_id
        self.resolved_at = datetime.now(timezone.utc)
        self.resolution_note = note


class ModerationLog(Base, TimestampMixin):
    """Log of all moderation actions."""

    __tablename__ = "moderation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Moderator who performed the action
    moderator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    
    # Action details
    action: Mapped[ModerationAction] = mapped_column(
        Enum(ModerationAction),
        nullable=False,
    )
    target_type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'user', 'ad', 'message'
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    
    # Additional context
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON for extra data
    
    # Related report (if action was triggered by a report)
    report_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("reports.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    moderator: Mapped[Optional["User"]] = relationship("User")

    def __repr__(self) -> str:
        return f"<ModerationLog(id={self.id}, action={self.action}, target={self.target_type}:{self.target_id})>"

