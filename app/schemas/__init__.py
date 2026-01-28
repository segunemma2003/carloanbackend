"""
Pydantic schemas for request/response validation.
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserProfileResponse,
    TokenResponse,
    SessionResponse,
)
from app.schemas.ad import (
    AdCreate,
    AdUpdate,
    AdResponse,
    AdListResponse,
    AdSearchParams,
)
from app.schemas.vehicle import (
    VehicleTypeResponse,
    BrandResponse,
    ModelResponse,
    GenerationResponse,
    ModificationResponse,
)
from app.schemas.category import CategoryResponse, CategoryCreate
from app.schemas.location import CountryResponse, RegionResponse, CityResponse
from app.schemas.chat import (
    DialogResponse,
    MessageCreate,
    MessageResponse,
)
from app.schemas.common import PaginatedResponse, MessageOut


__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "UserUpdate",
    "UserProfileResponse",
    "TokenResponse",
    "SessionResponse",
    # Ad
    "AdCreate",
    "AdUpdate",
    "AdResponse",
    "AdListResponse",
    "AdSearchParams",
    # Vehicle
    "VehicleTypeResponse",
    "BrandResponse",
    "ModelResponse",
    "GenerationResponse",
    "ModificationResponse",
    # Category
    "CategoryResponse",
    "CategoryCreate",
    # Location
    "CountryResponse",
    "RegionResponse",
    "CityResponse",
    # Chat
    "DialogResponse",
    "MessageCreate",
    "MessageResponse",
    # Common
    "PaginatedResponse",
    "MessageOut",
]

