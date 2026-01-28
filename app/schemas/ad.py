"""
Advertisement/Listing schemas.
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field

from app.models.ad import AdStatus, Condition, SteeringWheel, PTSType, Currency
from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse
from app.schemas.vehicle import (
    VehicleTypeResponse,
    BrandResponse,
    ModelResponse,
    GenerationResponse,
    ModificationResponse,
    BodyTypeResponse,
    TransmissionResponse,
    FuelTypeResponse,
    DriveTypeResponse,
    ColorResponse,
)
from app.schemas.category import CategoryResponse
from app.schemas.location import CityWithRegion


class AdImageResponse(BaseSchema):
    """Ad image response."""

    id: int
    url: str
    thumbnail_url: Optional[str] = None
    sort_order: int
    is_main: bool


class AdImageCreate(BaseModel):
    """Create ad image."""

    url: str
    thumbnail_url: Optional[str] = None
    sort_order: int = 0
    is_main: bool = False


class AdVideoResponse(BaseSchema):
    """Ad video response."""

    id: int
    url: str
    video_type: str
    thumbnail_url: Optional[str] = None


class AdVideoCreate(BaseModel):
    """Create ad video."""

    url: str
    video_type: str
    thumbnail_url: Optional[str] = None


class AdCreate(BaseModel):
    """Create ad schema."""

    # Category
    category_id: int
    
    # Vehicle references
    vehicle_type_id: int
    brand_id: int
    model_id: int
    generation_id: Optional[int] = None
    modification_id: Optional[int] = None
    
    # Basic specs
    year: int = Field(..., ge=1900, le=2030)
    mileage: int = Field(..., ge=0)
    
    # Optional specs (can be auto-filled from modification)
    body_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    drive_type_id: Optional[int] = None
    color_id: Optional[int] = None
    engine_volume: Optional[float] = Field(None, ge=0, le=20)
    engine_power: Optional[int] = Field(None, ge=0, le=2000)
    
    # Condition
    condition: Condition = Condition.USED
    is_damaged: bool = False
    
    # Documents
    vin: Optional[str] = Field(None, min_length=17, max_length=17)
    pts_type: Optional[PTSType] = None
    owners_count: Optional[int] = Field(None, ge=1, le=20)
    steering_wheel: SteeringWheel = SteeringWheel.LEFT
    
    # Price
    price: Decimal = Field(..., gt=0)
    currency: Currency = Currency.RUB
    price_negotiable: bool = False
    exchange_possible: bool = False
    
    # Description
    title: str = Field(..., min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    
    # Contact
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    show_phone: bool = True
    
    # Location
    city_id: int
    address: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Features
    features: Optional[List[str]] = None
    
    # Media
    images: List[AdImageCreate] = []
    videos: List[AdVideoCreate] = []


class AdUpdate(BaseModel):
    """Update ad schema."""

    category_id: Optional[int] = None
    vehicle_type_id: Optional[int] = None
    brand_id: Optional[int] = None
    model_id: Optional[int] = None
    generation_id: Optional[int] = None
    modification_id: Optional[int] = None
    year: Optional[int] = Field(None, ge=1900, le=2030)
    mileage: Optional[int] = Field(None, ge=0)
    body_type_id: Optional[int] = None
    transmission_id: Optional[int] = None
    fuel_type_id: Optional[int] = None
    drive_type_id: Optional[int] = None
    color_id: Optional[int] = None
    engine_volume: Optional[float] = Field(None, ge=0, le=20)
    engine_power: Optional[int] = Field(None, ge=0, le=2000)
    condition: Optional[Condition] = None
    is_damaged: Optional[bool] = None
    vin: Optional[str] = Field(None, min_length=17, max_length=17)
    pts_type: Optional[PTSType] = None
    owners_count: Optional[int] = Field(None, ge=1, le=20)
    steering_wheel: Optional[SteeringWheel] = None
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[Currency] = None
    price_negotiable: Optional[bool] = None
    exchange_possible: Optional[bool] = None
    title: Optional[str] = Field(None, min_length=5, max_length=255)
    description: Optional[str] = Field(None, max_length=10000)
    contact_name: Optional[str] = Field(None, max_length=100)
    contact_phone: Optional[str] = Field(None, max_length=20)
    show_phone: Optional[bool] = None
    city_id: Optional[int] = None
    address: Optional[str] = Field(None, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    features: Optional[List[str]] = None


class AdResponse(BaseSchema):
    """Full ad response."""

    id: int
    status: AdStatus
    
    # Owner
    user_id: int
    user: UserResponse
    
    # Category
    category_id: int
    category: CategoryResponse
    
    # Vehicle info
    vehicle_type_id: int
    vehicle_type: VehicleTypeResponse
    brand_id: int
    brand: BrandResponse
    model_id: int
    model: ModelResponse
    generation_id: Optional[int] = None
    generation: Optional[GenerationResponse] = None
    modification_id: Optional[int] = None
    modification: Optional[ModificationResponse] = None
    
    # Specs
    year: int
    mileage: int
    body_type_id: Optional[int] = None
    body_type: Optional[BodyTypeResponse] = None
    transmission_id: Optional[int] = None
    transmission: Optional[TransmissionResponse] = None
    fuel_type_id: Optional[int] = None
    fuel_type: Optional[FuelTypeResponse] = None
    drive_type_id: Optional[int] = None
    drive_type: Optional[DriveTypeResponse] = None
    color_id: Optional[int] = None
    color: Optional[ColorResponse] = None
    engine_volume: Optional[float] = None
    engine_power: Optional[int] = None
    
    # Condition
    condition: Condition
    is_damaged: bool
    
    # Documents
    vin: Optional[str] = None
    pts_type: Optional[PTSType] = None
    owners_count: Optional[int] = None
    steering_wheel: SteeringWheel
    
    # Price
    price: Decimal
    currency: Currency
    price_negotiable: bool
    exchange_possible: bool
    
    # Description
    title: str
    description: Optional[str] = None
    
    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    show_phone: bool
    
    # Location
    city_id: int
    city: CityWithRegion
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Features
    features: Optional[List[str]] = None
    
    # Media
    images: List[AdImageResponse] = []
    videos: List[AdVideoResponse] = []
    
    # Dates
    published_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Statistics
    views_count: int
    favorites_count: int
    
    # Paid services
    is_featured: bool
    is_top: bool
    is_urgent: bool
    
    # User-specific (filled at runtime)
    is_favorite: bool = False
    is_in_comparison: bool = False


class AdListResponse(BaseSchema):
    """Ad response for list views (simplified)."""

    id: int
    status: AdStatus
    user_id: int
    
    # Basic info
    title: str
    price: Decimal
    currency: Currency
    year: int
    mileage: int
    
    # Main image
    main_image_url: Optional[str] = None
    
    # Vehicle
    brand_name: str
    model_name: str
    generation_name: Optional[str] = None
    
    # Specs
    engine_volume: Optional[float] = None
    engine_power: Optional[int] = None
    transmission_name: Optional[str] = None
    fuel_type_name: Optional[str] = None
    
    # Location
    city_name: str
    region_name: str
    
    # Dates
    published_at: Optional[datetime] = None
    created_at: datetime
    
    # Stats
    views_count: int
    
    # Paid services
    is_featured: bool
    is_top: bool
    is_urgent: bool
    
    # User-specific
    is_favorite: bool = False


class AdSearchParams(BaseModel):
    """Search parameters for ads."""

    # Text search
    q: Optional[str] = None
    
    # Category
    category_id: Optional[int] = None
    
    # Vehicle filters
    vehicle_type_id: Optional[int] = None
    brand_id: Optional[int] = None
    brand_ids: Optional[List[int]] = None
    model_id: Optional[int] = None
    model_ids: Optional[List[int]] = None
    generation_id: Optional[int] = None
    
    # Price
    price_from: Optional[Decimal] = None
    price_to: Optional[Decimal] = None
    currency: Optional[Currency] = None
    
    # Year
    year_from: Optional[int] = None
    year_to: Optional[int] = None
    
    # Mileage
    mileage_from: Optional[int] = None
    mileage_to: Optional[int] = None
    
    # Specs
    body_type_id: Optional[int] = None
    body_type_ids: Optional[List[int]] = None
    transmission_id: Optional[int] = None
    transmission_ids: Optional[List[int]] = None
    fuel_type_id: Optional[int] = None
    fuel_type_ids: Optional[List[int]] = None
    drive_type_id: Optional[int] = None
    drive_type_ids: Optional[List[int]] = None
    color_id: Optional[int] = None
    color_ids: Optional[List[int]] = None
    
    # Engine
    engine_volume_from: Optional[float] = None
    engine_volume_to: Optional[float] = None
    engine_power_from: Optional[int] = None
    engine_power_to: Optional[int] = None
    
    # Condition
    condition: Optional[Condition] = None
    is_damaged: Optional[bool] = None
    steering_wheel: Optional[SteeringWheel] = None
    
    # Location
    city_id: Optional[int] = None
    region_id: Optional[int] = None
    radius_km: Optional[int] = None  # Radius from city center
    
    # Other filters
    has_photo: Optional[bool] = None
    has_video: Optional[bool] = None
    has_vin: Optional[bool] = None
    dealer_only: Optional[bool] = None
    private_only: Optional[bool] = None
    
    # Sorting
    sort_by: str = "date"  # date, price_asc, price_desc, mileage, year
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class AdModerationAction(BaseModel):
    """Moderation action on an ad."""

    action: str  # "approve", "reject"
    reason: Optional[str] = None


class AdStats(BaseModel):
    """Ad statistics."""

    views_count: int
    favorites_count: int
    messages_count: int
    phone_views_count: int
    views_today: int
    views_week: int
    views_month: int

