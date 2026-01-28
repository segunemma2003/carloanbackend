"""
Favorites, comparison, and view history models.
"""

from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ad import Ad


class Favorite(Base, TimestampMixin):
    """User's favorite ads."""

    __tablename__ = "favorites"
    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_user_ad_favorite"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    ad: Mapped["Ad"] = relationship("Ad", back_populates="favorites")

    def __repr__(self) -> str:
        return f"<Favorite(id={self.id}, user_id={self.user_id}, ad_id={self.ad_id})>"


class Comparison(Base, TimestampMixin):
    """User's comparison list."""

    __tablename__ = "comparisons"
    __table_args__ = (
        UniqueConstraint("user_id", "ad_id", name="uq_user_ad_comparison"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="comparisons")
    ad: Mapped["Ad"] = relationship("Ad", back_populates="comparisons")

    def __repr__(self) -> str:
        return f"<Comparison(id={self.id}, user_id={self.user_id}, ad_id={self.ad_id})>"


class ViewHistory(Base):
    """User's ad view history."""

    __tablename__ = "view_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="view_history")
    ad: Mapped["Ad"] = relationship("Ad")

    def __repr__(self) -> str:
        return f"<ViewHistory(id={self.id}, user_id={self.user_id}, ad_id={self.ad_id})>"

