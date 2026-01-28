"""
Database models for AVTO LAIF.
All models are imported here for easy access and Alembic migrations.
"""

from app.models.user import User, UserSession, UserRole, AccountType
from app.models.category import Category
from app.models.vehicle import (
    VehicleType,
    Brand,
    Model,
    Generation,
    Modification,
    BodyType,
    Transmission,
    FuelType,
    DriveType,
    Color,
)
from app.models.location import Country, Region, City
from app.models.ad import Ad, AdStatus, AdImage, AdVideo
from app.models.chat import Dialog, Message
from app.models.favorites import Favorite, Comparison, ViewHistory
from app.models.moderation import Report, ModerationLog


__all__ = [
    # User
    "User",
    "UserSession",
    "UserRole",
    "AccountType",
    # Category
    "Category",
    # Vehicle
    "VehicleType",
    "Brand",
    "Model",
    "Generation",
    "Modification",
    "BodyType",
    "Transmission",
    "FuelType",
    "DriveType",
    "Color",
    # Location
    "Country",
    "Region",
    "City",
    # Ad
    "Ad",
    "AdStatus",
    "AdImage",
    "AdVideo",
    # Chat
    "Dialog",
    "Message",
    # Favorites
    "Favorite",
    "Comparison",
    "ViewHistory",
    # Moderation
    "Report",
    "ModerationLog",
]

