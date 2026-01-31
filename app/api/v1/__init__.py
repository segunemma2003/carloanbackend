"""
API v1 routes.
"""

from fastapi import APIRouter

from app.api.v1 import auth, users, ads, categories, vehicles, locations, chat, favorites, moderation, banners, uploads, admin_dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(ads.router, prefix="/ads", tags=["Advertisements"])
api_router.include_router(categories.router, prefix="/categories", tags=["Categories"])
api_router.include_router(vehicles.router, prefix="/vehicles", tags=["Vehicles"])
api_router.include_router(locations.router, prefix="/locations", tags=["Locations"])
api_router.include_router(chat.router, prefix="/chat", tags=["Chat"])
api_router.include_router(favorites.router, prefix="/favorites", tags=["Favorites"])
api_router.include_router(moderation.router, prefix="/moderation", tags=["Moderation"])
api_router.include_router(banners.router, prefix="/banners", tags=["Banners"])
api_router.include_router(uploads.router, prefix="/uploads", tags=["Uploads"])
api_router.include_router(admin_dashboard.router, prefix="/admin", tags=["Admin Dashboard"])

