"""
Category model for organizing ads.
Supports hierarchical categories with SEO data.
"""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.ad import Ad


class Category(Base, TimestampMixin):
    """
    Category model with hierarchical support.
    
    Top-level categories have parent_id = None.
    Examples: Auto, Trucks, Motorcycles, Boats, Rent, etc.
    """

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Icon class or URL
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Hierarchy
    parent_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)  # 0 = top level
    
    # Ordering and visibility
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    show_in_menu: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # SEO
    seo_title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    seo_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    seo_h1: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    seo_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Statistics (cached, updated periodically)
    ads_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Relationships
    parent: Mapped[Optional["Category"]] = relationship(
        "Category",
        remote_side="Category.id",
        back_populates="children",
    )
    children: Mapped[List["Category"]] = relationship(
        "Category",
        back_populates="parent",
        cascade="all, delete-orphan",
    )
    ads: Mapped[List["Ad"]] = relationship("Ad", back_populates="category")

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name={self.name}, slug={self.slug})>"

    @property
    def is_top_level(self) -> bool:
        return self.parent_id is None

    @property
    def full_path(self) -> str:
        """Get full category path (e.g., 'Auto / Sedans')."""
        if self.parent:
            return f"{self.parent.full_path} / {self.name}"
        return self.name

