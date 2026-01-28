"""
Advertisement/Listing models.
Core model for vehicle listings with all specifications.
"""

import enum
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.category import Category
    from app.models.vehicle import (
        VehicleType, Brand, Model, Generation, Modification,
        BodyType, Transmission, FuelType, DriveType, Color,
    )
    from app.models.location import City
    from app.models.chat import Dialog
    from app.models.favorites import Favorite, Comparison


class AdStatus(str, enum.Enum):
    """Advertisement status."""
    DRAFT = "draft"
    PENDING = "pending"  # Awaiting moderation
    ACTIVE = "active"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    SOLD = "sold"
    EXPIRED = "expired"


class Condition(str, enum.Enum):
    """Vehicle condition."""
    NEW = "new"
    USED = "used"
    DAMAGED = "damaged"
    FOR_PARTS = "for_parts"


class SteeringWheel(str, enum.Enum):
    """Steering wheel position."""
    LEFT = "left"
    RIGHT = "right"


class PTSType(str, enum.Enum):
    """PTS (vehicle passport) type."""
    ORIGINAL = "original"
    DUPLICATE = "duplicate"
    ELECTRONIC = "electronic"


class Currency(str, enum.Enum):
    """Supported currencies."""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"


class Ad(Base, TimestampMixin, SoftDeleteMixin):
    """
    Main advertisement model.
    Contains all vehicle listing information.
    """

    __tablename__ = "ads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Owner
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    # Status
    status: Mapped[AdStatus] = mapped_column(
        Enum(AdStatus),
        default=AdStatus.DRAFT,
        nullable=False,
        index=True,
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    moderated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    moderated_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Category
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    
    # Vehicle info - References
    vehicle_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicle_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    brand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("brands.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    generation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("generations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    modification_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("modifications.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Vehicle specifications
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    mileage: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # in km
    
    body_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("body_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    transmission_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("transmissions.id", ondelete="SET NULL"),
        nullable=True,
    )
    fuel_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("fuel_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    drive_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("drive_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    color_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("colors.id", ondelete="SET NULL"),
        nullable=True,
    )
    
    # Engine details (can be auto-filled from modification or entered manually)
    engine_volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    engine_power: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Condition
    condition: Mapped[Condition] = mapped_column(
        Enum(Condition),
        default=Condition.USED,
        nullable=False,
    )
    is_damaged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Documents
    vin: Mapped[Optional[str]] = mapped_column(String(17), nullable=True, index=True)
    pts_type: Mapped[Optional[PTSType]] = mapped_column(Enum(PTSType), nullable=True)
    owners_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Steering
    steering_wheel: Mapped[SteeringWheel] = mapped_column(
        Enum(SteeringWheel),
        default=SteeringWheel.LEFT,
        nullable=False,
    )
    
    # Price
    price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        index=True,
    )
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency),
        default=Currency.RUB,
        nullable=False,
    )
    price_negotiable: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    exchange_possible: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Description
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Contact info (can differ from user's main contact)
    contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    show_phone: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Location
    city_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("cities.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Features/Equipment (stored as JSON or separate table)
    features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    # Dates
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Statistics
    views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    favorites_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    messages_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    phone_views_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Paid services flags
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_top: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    featured_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    top_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="ads")
    category: Mapped["Category"] = relationship("Category", back_populates="ads")
    vehicle_type: Mapped["VehicleType"] = relationship("VehicleType")
    brand: Mapped["Brand"] = relationship("Brand")
    model: Mapped["Model"] = relationship("Model")
    generation: Mapped[Optional["Generation"]] = relationship("Generation")
    modification: Mapped[Optional["Modification"]] = relationship("Modification")
    body_type: Mapped[Optional["BodyType"]] = relationship("BodyType")
    transmission: Mapped[Optional["Transmission"]] = relationship("Transmission")
    fuel_type: Mapped[Optional["FuelType"]] = relationship("FuelType")
    drive_type: Mapped[Optional["DriveType"]] = relationship("DriveType")
    color: Mapped[Optional["Color"]] = relationship("Color")
    city: Mapped["City"] = relationship("City", back_populates="ads")
    images: Mapped[List["AdImage"]] = relationship(
        "AdImage",
        back_populates="ad",
        cascade="all, delete-orphan",
        order_by="AdImage.sort_order",
    )
    videos: Mapped[List["AdVideo"]] = relationship(
        "AdVideo",
        back_populates="ad",
        cascade="all, delete-orphan",
    )
    dialogs: Mapped[List["Dialog"]] = relationship("Dialog", back_populates="ad")
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite",
        back_populates="ad",
        cascade="all, delete-orphan",
    )
    comparisons: Mapped[List["Comparison"]] = relationship(
        "Comparison",
        back_populates="ad",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Ad(id={self.id}, title={self.title}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        return self.status == AdStatus.ACTIVE

    @property
    def main_image_url(self) -> Optional[str]:
        """Get the main (first) image URL."""
        if self.images:
            return self.images[0].url
        return None


class AdImage(Base, TimestampMixin):
    """Ad image model."""

    __tablename__ = "ad_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_main: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad", back_populates="images")

    def __repr__(self) -> str:
        return f"<AdImage(id={self.id}, ad_id={self.ad_id})>"


class AdVideo(Base, TimestampMixin):
    """Ad video model (YouTube/external links or uploaded)."""

    __tablename__ = "ad_videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ad_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("ads.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    video_type: Mapped[str] = mapped_column(String(50), nullable=False)  # youtube, vimeo, uploaded
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Relationships
    ad: Mapped["Ad"] = relationship("Ad", back_populates="videos")

    def __repr__(self) -> str:
        return f"<AdVideo(id={self.id}, ad_id={self.ad_id})>"

