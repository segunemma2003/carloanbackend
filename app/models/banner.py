"""
Banner management models for admin.
"""

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin


class BannerType(str, enum.Enum):
    """Banner display type."""
    HEADER = "header"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    MODAL = "modal"
    BETWEEN_ADS = "between_ads"


class BannerStatus(str, enum.Enum):
    """Banner status."""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    EXPIRED = "expired"


class Banner(Base, TimestampMixin):
    """Banner/Advertisement management."""

    __tablename__ = "banners"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Banner details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Display
    banner_type: Mapped[BannerType] = mapped_column(
        Enum(BannerType),
        default=BannerType.SIDEBAR,
        nullable=False,
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    link_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Status and scheduling
    status: Mapped[BannerStatus] = mapped_column(
        Enum(BannerStatus),
        default=BannerStatus.DRAFT,
        nullable=False,
    )
    start_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    end_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    # Priority and stats
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    impressions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Targeting (optional for future)
    target_pages: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    def __repr__(self) -> str:
        return f"<Banner(id={self.id}, title={self.title}, type={self.banner_type})>"

