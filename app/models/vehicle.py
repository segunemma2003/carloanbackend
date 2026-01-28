"""
Vehicle reference models.
Implements the hierarchical vehicle catalog:
VehicleType -> Brand -> Model -> Generation -> Modification
"""

from typing import Optional, List, TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin

if TYPE_CHECKING:
    from app.models.ad import Ad


class VehicleType(Base, TimestampMixin):
    """
    Vehicle type (e.g., Passenger, Commercial, Motorcycle, Special equipment).
    """

    __tablename__ = "vehicle_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    brands: Mapped[List["Brand"]] = relationship("Brand", back_populates="vehicle_type")

    def __repr__(self) -> str:
        return f"<VehicleType(id={self.id}, name={self.name})>"


class Brand(Base, TimestampMixin):
    """Vehicle brand (e.g., Toyota, BMW, Yamaha)."""

    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("vehicle_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    logo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    vehicle_type: Mapped["VehicleType"] = relationship("VehicleType", back_populates="brands")
    models: Mapped[List["Model"]] = relationship("Model", back_populates="brand")

    def __repr__(self) -> str:
        return f"<Brand(id={self.id}, name={self.name})>"


class Model(Base, TimestampMixin):
    """Vehicle model (e.g., Camry, 3 Series, YZF-R1)."""

    __tablename__ = "models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    brand_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("brands.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_popular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    brand: Mapped["Brand"] = relationship("Brand", back_populates="models")
    generations: Mapped[List["Generation"]] = relationship("Generation", back_populates="model")

    def __repr__(self) -> str:
        return f"<Model(id={self.id}, name={self.name})>"


class Generation(Base, TimestampMixin):
    """
    Vehicle generation (e.g., XV70, G20).
    Represents a specific version/facelift of a model.
    """

    __tablename__ = "generations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # None = still in production
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    model: Mapped["Model"] = relationship("Model", back_populates="generations")
    modifications: Mapped[List["Modification"]] = relationship(
        "Modification",
        back_populates="generation",
    )

    def __repr__(self) -> str:
        return f"<Generation(id={self.id}, name={self.name})>"

    @property
    def year_range(self) -> str:
        if self.year_end:
            return f"{self.year_start}-{self.year_end}"
        return f"{self.year_start}-н.в."


class Modification(Base, TimestampMixin):
    """
    Vehicle modification (specific engine/transmission configuration).
    Contains detailed technical specifications.
    """

    __tablename__ = "modifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    generation_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("generations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False, index=True)

    # Engine
    engine_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    engine_volume: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in liters
    engine_power_hp: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engine_power_kw: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    engine_torque: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Nm

    # Fuel
    fuel_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("fuel_types.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Transmission
    transmission_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("transmissions.id", ondelete="SET NULL"),
        nullable=True,
    )
    gears_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Drive
    drive_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("drive_types.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Body
    body_type_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("body_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    doors_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    seats_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Performance
    acceleration_0_100: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # seconds
    max_speed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # km/h
    fuel_consumption_city: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_consumption_highway: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    fuel_consumption_combined: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Dimensions
    length: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # mm
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    wheelbase: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    clearance: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    trunk_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # liters
    fuel_tank_volume: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    curb_weight: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # kg

    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    generation: Mapped["Generation"] = relationship("Generation", back_populates="modifications")
    fuel_type: Mapped[Optional["FuelType"]] = relationship("FuelType")
    transmission: Mapped[Optional["Transmission"]] = relationship("Transmission")
    drive_type: Mapped[Optional["DriveType"]] = relationship("DriveType")
    body_type: Mapped[Optional["BodyType"]] = relationship("BodyType")

    def __repr__(self) -> str:
        return f"<Modification(id={self.id}, name={self.name})>"


class BodyType(Base, TimestampMixin):
    """Body type reference (Sedan, Hatchback, SUV, etc.)."""

    __tablename__ = "body_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    icon: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<BodyType(id={self.id}, name={self.name})>"


class Transmission(Base, TimestampMixin):
    """Transmission type reference (Manual, Automatic, CVT, etc.)."""

    __tablename__ = "transmissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Transmission(id={self.id}, name={self.name})>"


class FuelType(Base, TimestampMixin):
    """Fuel type reference (Petrol, Diesel, Electric, Hybrid, etc.)."""

    __tablename__ = "fuel_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<FuelType(id={self.id}, name={self.name})>"


class DriveType(Base, TimestampMixin):
    """Drive type reference (FWD, RWD, AWD, 4WD)."""

    __tablename__ = "drive_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    short_name: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<DriveType(id={self.id}, name={self.name})>"


class Color(Base, TimestampMixin):
    """Vehicle color reference."""

    __tablename__ = "colors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    hex_code: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # #RRGGBB
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<Color(id={self.id}, name={self.name})>"

