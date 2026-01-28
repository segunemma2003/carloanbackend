"""
Location schemas.
"""

from typing import Optional, List

from pydantic import BaseModel

from app.schemas.common import BaseSchema


class CountryResponse(BaseSchema):
    """Country response."""

    id: int
    name: str
    slug: str
    code: str
    phone_code: Optional[str] = None
    flag_emoji: Optional[str] = None


class CountryCreate(BaseModel):
    """Create country."""

    name: str
    slug: str
    code: str
    phone_code: Optional[str] = None
    flag_emoji: Optional[str] = None
    sort_order: int = 0


class RegionResponse(BaseSchema):
    """Region response."""

    id: int
    country_id: int
    name: str
    slug: str
    code: Optional[str] = None


class RegionCreate(BaseModel):
    """Create region."""

    country_id: int
    name: str
    slug: str
    code: Optional[str] = None
    sort_order: int = 0


class CityResponse(BaseSchema):
    """City response."""

    id: int
    region_id: int
    name: str
    slug: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_major: bool


class CityCreate(BaseModel):
    """Create city."""

    region_id: int
    name: str
    slug: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    is_major: bool = False
    sort_order: int = 0


class CityWithRegion(CityResponse):
    """City with region info."""

    region_name: str
    country_name: str


class LocationSuggestion(BaseModel):
    """Location suggestion for autocomplete."""

    id: int
    name: str
    full_name: str  # "City, Region"
    type: str  # "city" or "region"


class GeoLocation(BaseModel):
    """Geolocation coordinates."""

    latitude: float
    longitude: float
    accuracy: Optional[float] = None


class LocationDetectionResult(BaseModel):
    """Result of location detection."""

    city: Optional[CityResponse] = None
    region: Optional[RegionResponse] = None
    country: Optional[CountryResponse] = None
    detected_by: str  # "ip", "gps", "manual"


class RegionWithCities(RegionResponse):
    """Region with nested cities."""

    cities: List[CityResponse] = []


class CountryWithRegions(CountryResponse):
    """Country with nested regions."""

    regions: List[RegionWithCities] = []

