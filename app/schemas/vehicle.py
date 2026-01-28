"""
Vehicle reference schemas.
"""

from typing import Optional, List

from pydantic import BaseModel

from app.schemas.common import BaseSchema


class VehicleTypeResponse(BaseSchema):
    """Vehicle type response."""

    id: int
    name: str
    slug: str
    icon: Optional[str] = None
    sort_order: int


class VehicleTypeCreate(BaseModel):
    """Create vehicle type."""

    name: str
    slug: str
    icon: Optional[str] = None
    sort_order: int = 0


class BrandResponse(BaseSchema):
    """Brand response."""

    id: int
    vehicle_type_id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    country: Optional[str] = None
    is_popular: bool


class BrandCreate(BaseModel):
    """Create brand."""

    vehicle_type_id: int
    name: str
    slug: str
    logo_url: Optional[str] = None
    country: Optional[str] = None
    is_popular: bool = False
    sort_order: int = 0


class ModelResponse(BaseSchema):
    """Model response."""

    id: int
    brand_id: int
    name: str
    slug: str
    is_popular: bool


class ModelCreate(BaseModel):
    """Create model."""

    brand_id: int
    name: str
    slug: str
    is_popular: bool = False
    sort_order: int = 0


class GenerationResponse(BaseSchema):
    """Generation response."""

    id: int
    model_id: int
    name: str
    slug: str
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    image_url: Optional[str] = None


class GenerationCreate(BaseModel):
    """Create generation."""

    model_id: int
    name: str
    slug: str
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    image_url: Optional[str] = None
    sort_order: int = 0


class ModificationResponse(BaseSchema):
    """Modification response with full specs."""

    id: int
    generation_id: int
    name: str
    slug: str
    
    # Engine
    engine_type: Optional[str] = None
    engine_volume: Optional[float] = None
    engine_power_hp: Optional[int] = None
    engine_power_kw: Optional[int] = None
    engine_torque: Optional[int] = None
    
    # Fuel
    fuel_type_id: Optional[int] = None
    fuel_type_name: Optional[str] = None
    
    # Transmission
    transmission_id: Optional[int] = None
    transmission_name: Optional[str] = None
    gears_count: Optional[int] = None
    
    # Drive
    drive_type_id: Optional[int] = None
    drive_type_name: Optional[str] = None
    
    # Body
    body_type_id: Optional[int] = None
    body_type_name: Optional[str] = None
    doors_count: Optional[int] = None
    seats_count: Optional[int] = None
    
    # Performance
    acceleration_0_100: Optional[float] = None
    max_speed: Optional[int] = None
    fuel_consumption_city: Optional[float] = None
    fuel_consumption_highway: Optional[float] = None
    fuel_consumption_combined: Optional[float] = None
    
    # Dimensions
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    wheelbase: Optional[int] = None
    clearance: Optional[int] = None
    trunk_volume: Optional[int] = None
    fuel_tank_volume: Optional[int] = None
    curb_weight: Optional[int] = None


class ModificationCreate(BaseModel):
    """Create modification."""

    generation_id: int
    name: str
    slug: str
    engine_type: Optional[str] = None
    engine_volume: Optional[float] = None
    engine_power_hp: Optional[int] = None
    engine_power_kw: Optional[int] = None
    engine_torque: Optional[int] = None
    fuel_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    gears_count: Optional[int] = None
    drive_type_id: Optional[int] = None
    body_type_id: Optional[int] = None
    doors_count: Optional[int] = None
    seats_count: Optional[int] = None
    acceleration_0_100: Optional[float] = None
    max_speed: Optional[int] = None
    fuel_consumption_city: Optional[float] = None
    fuel_consumption_highway: Optional[float] = None
    fuel_consumption_combined: Optional[float] = None
    length: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    wheelbase: Optional[int] = None
    clearance: Optional[int] = None
    trunk_volume: Optional[int] = None
    fuel_tank_volume: Optional[int] = None
    curb_weight: Optional[int] = None
    sort_order: int = 0


class BodyTypeResponse(BaseSchema):
    """Body type response."""

    id: int
    name: str
    slug: str
    icon: Optional[str] = None


class TransmissionResponse(BaseSchema):
    """Transmission response."""

    id: int
    name: str
    slug: str
    short_name: Optional[str] = None


class FuelTypeResponse(BaseSchema):
    """Fuel type response."""

    id: int
    name: str
    slug: str


class DriveTypeResponse(BaseSchema):
    """Drive type response."""

    id: int
    name: str
    slug: str
    short_name: Optional[str] = None


class ColorResponse(BaseSchema):
    """Color response."""

    id: int
    name: str
    slug: str
    hex_code: Optional[str] = None


# Cascading selection responses
class BrandWithModelsResponse(BrandResponse):
    """Brand with nested models."""

    models: List[ModelResponse] = []


class ModelWithGenerationsResponse(ModelResponse):
    """Model with nested generations."""

    generations: List[GenerationResponse] = []


class GenerationWithModificationsResponse(GenerationResponse):
    """Generation with nested modifications."""

    modifications: List[ModificationResponse] = []


class VehicleFullHierarchy(BaseModel):
    """Full vehicle hierarchy for cascading selection."""

    vehicle_types: List[VehicleTypeResponse]
    brands: List[BrandResponse]
    body_types: List[BodyTypeResponse]
    transmissions: List[TransmissionResponse]
    fuel_types: List[FuelTypeResponse]
    drive_types: List[DriveTypeResponse]
    colors: List[ColorResponse]

