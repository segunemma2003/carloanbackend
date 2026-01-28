"""
Location models for geolocation support.
Country -> Region -> City hierarchy.
"""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.ad import Ad


class Country(Base, TimestampMixin):
    """Country reference."""

    __tablename__ = "countries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(3), unique=True, nullable=False)  # ISO 3166-1 alpha-2/3
    phone_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    flag_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    regions: Mapped[List["Region"]] = relationship("Region", back_populates="country")

    def __repr__(self) -> str:
        return f"<Country(id={self.id}, name={self.name}, code={self.code})>"


class Region(Base, TimestampMixin):
    """Region/State/Oblast reference."""

    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    country_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # Region code
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    country: Mapped["Country"] = relationship("Country", back_populates="regions")
    cities: Mapped[List["City"]] = relationship("City", back_populates="region")

    def __repr__(self) -> str:
        return f"<Region(id={self.id}, name={self.name})>"


class City(Base, TimestampMixin):
    """City reference with coordinates."""

    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    region_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("regions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    
    # Coordinates for distance calculations
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Population for sorting/relevance
    population: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_major: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)  # Major city flag
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    region: Mapped["Region"] = relationship("Region", back_populates="cities")
    users: Mapped[List["User"]] = relationship("User", back_populates="city")
    ads: Mapped[List["Ad"]] = relationship("Ad", back_populates="city")

    def __repr__(self) -> str:
        return f"<City(id={self.id}, name={self.name})>"

    @property
    def full_name(self) -> str:
        """Get full location name (City, Region)."""
        return f"{self.name}, {self.region.name}"

    @property
    def coordinates(self) -> tuple[float, float] | None:
        """Get coordinates as tuple."""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None

