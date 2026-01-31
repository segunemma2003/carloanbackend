"""
SQLAdmin configuration for AVTO LAIF Admin Panel.
Beautiful admin interface for managing all application data.
"""

from sqladmin import Admin, ModelView
from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse, HTMLResponse

from app.core.database import engine
from app.core.security import verify_password
from app.models.user import User, UserRole, UserSession
from app.models.category import Category
from app.models.vehicle import (
    VehicleType, Brand, Model, Generation, Modification,
    BodyType, Transmission, FuelType, DriveType, Color
)
from app.models.location import Country, Region, City
from app.models.ad import Ad, AdImage, AdVideo
from app.models.chat import Dialog, Message
from app.models.favorites import Favorite, Comparison, ViewHistory
from app.models.moderation import Report, ModerationLog
from app.models.banner import Banner
from app.admin_views import (
    add_user_labels, add_session_labels, add_category_labels,
    add_vehicle_labels, add_location_labels, add_ad_labels,
    add_ad_media_labels, add_chat_labels, add_moderation_labels,
    add_banner_labels
)


class AdminAuth(AuthenticationBackend):
    """
    Authentication backend for admin panel.
    Only allows users with ADMIN role.
    """
    
    async def login(self, request: Request) -> bool:
        """Handle login."""
        form = await request.form()
        email = form.get("username")
        password = form.get("password")
        
        print(f"[ADMIN LOGIN] Attempting login for: {email}")
        
        # Import here to avoid circular dependency
        from sqlalchemy import select
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"[ADMIN LOGIN] User not found: {email}")
                return False
            
            print(f"[ADMIN LOGIN] User found: {user.email}, Role: {user.role}")
            
            if not verify_password(password, user.password_hash):
                print(f"[ADMIN LOGIN] Password verification failed")
                return False
            
            print(f"[ADMIN LOGIN] Password verified successfully")
            
            if user.role != UserRole.ADMIN:
                print(f"[ADMIN LOGIN] User is not ADMIN role: {user.role}")
                return False
            
            print(f"[ADMIN LOGIN] Role check passed, storing session")
            
            # Store user info in session
            # SQLAdmin uses a specific session key format
            request.session["user_id"] = user.id
            request.session["user_email"] = user.email
            request.session["user_name"] = user.name
            
            # Force session save by accessing it
            # Starlette's SessionMiddleware automatically saves when modified
            session_keys = list(request.session.keys())
            print(f"[ADMIN LOGIN] Session stored: user_id={user.id}")
            print(f"[ADMIN LOGIN] Session keys: {session_keys}")
            print(f"[ADMIN LOGIN] Session cookie name: avto_laif_session")
            print(f"[ADMIN LOGIN] Login successful for {email}")
            
            # Return True - SQLAdmin will handle the redirect
            return True
    
    async def logout(self, request: Request) -> bool:
        """Handle logout."""
        request.session.clear()
        return True
    
    async def authenticate(self, request: Request) -> bool:
        """Check if user is authenticated."""
        user_id = request.session.get("user_id")
        
        if not user_id:
            print(f"[ADMIN AUTH] No user_id in session. Session keys: {list(request.session.keys())}")
            return False
        
        # Verify user still exists and is admin
        from sqlalchemy import select
        from app.core.database import async_session_maker
        
        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(User).where(User.id == user_id)
                )
                user = result.scalar_one_or_none()
                
                if not user:
                    print(f"[ADMIN AUTH] User {user_id} not found in database")
                    request.session.clear()
                    return False
                
                if user.role != UserRole.ADMIN:
                    print(f"[ADMIN AUTH] User {user_id} is not ADMIN (role: {user.role})")
                    request.session.clear()
                    return False
                
                if not user.is_active:
                    print(f"[ADMIN AUTH] User {user_id} is not active")
                    request.session.clear()
                    return False
                
                print(f"[ADMIN AUTH] Authentication successful for user {user_id}")
                return True
        except Exception as e:
            print(f"[ADMIN AUTH] Error during authentication: {e}")
            import traceback
            traceback.print_exc()
            return False


# ============ User Management ============

class UserAdmin(ModelView, model=User):
    """Admin view for users."""
    
    name = "User Account"
    name_plural = "User Accounts"
    icon = "fa-solid fa-users"
    
    # List view
    column_list = [
        User.id, User.email, User.name, User.role, User.account_type,
        User.email_verified, User.phone_verified, User.is_active,
        User.created_at
    ]
    column_searchable_list = [User.email, User.name, User.phone]
    column_sortable_list = [User.id, User.email, User.created_at]
    column_default_sort = [(User.created_at, True)]
    
    # Filters
    column_filters = [User.role, User.account_type, User.is_active, User.email_verified]
    
    # Form
    form_columns = [
        User.email, User.name, User.phone, User.role, User.account_type,
        User.company_name, User.company_description, User.company_website,
        User.email_verified, User.phone_verified, User.is_active
    ]
    
    # Details
    column_details_list = [
        User.id, User.email, User.name, User.phone, User.role,
        User.account_type, User.company_name, User.company_description,
        User.company_website, User.email_verified, User.phone_verified,
        User.is_active, User.created_at, User.updated_at
    ]
    
    # Permissions
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    
    # Labels - will be set after class definition
    pass


# Apply labels after class definition
add_user_labels(UserAdmin)


class UserSessionAdmin(ModelView, model=UserSession):
    """Admin view for user sessions."""
    
    name = "User Session"
    name_plural = "Active Sessions"
    icon = "fa-solid fa-key"
    
    column_list = [
        UserSession.id, UserSession.user_id, UserSession.ip_address,
        UserSession.user_agent, UserSession.revoked, UserSession.created_at,
        UserSession.last_used_at
    ]
    column_searchable_list = [UserSession.ip_address, UserSession.user_agent]
    column_filters = [UserSession.revoked, UserSession.user_id]
    
    can_create = False
    can_edit = False
    can_delete = True


# Apply labels
add_session_labels(UserSessionAdmin)


# ============ Categories ============

class CategoryAdmin(ModelView, model=Category):
    """Admin view for categories."""
    
    name = "Category"
    name_plural = "Product Categories"
    icon = "fa-solid fa-tags"
    
    column_list = [
        Category.id, Category.name, Category.slug, Category.parent_id,
        Category.level, Category.is_active, Category.sort_order
    ]
    column_searchable_list = [Category.name, Category.slug]
    column_sortable_list = [Category.id, Category.name, Category.sort_order]
    column_filters = [Category.is_active, Category.level]
    
    form_columns = [
        Category.name, Category.slug, Category.parent_id, Category.icon,
        Category.image_url, Category.description, Category.seo_title, Category.seo_description,
        Category.seo_h1, Category.seo_text, Category.is_active, Category.sort_order
    ]
    
    # Configure dropdown for parent_id
    form_ajax_refs = {
        "parent": {
            "fields": ("name",),
            "order_by": "name",
        }
    }
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_category_labels(CategoryAdmin)


# ============ Vehicle References ============

class VehicleTypeAdmin(ModelView, model=VehicleType):
    """Admin view for vehicle types."""
    
    name = "Vehicle Type"
    name_plural = "Vehicle Categories"
    icon = "fa-solid fa-car"
    
    column_list = [VehicleType.id, VehicleType.name, VehicleType.slug, VehicleType.is_active, VehicleType.sort_order]
    column_searchable_list = [VehicleType.name, VehicleType.slug]
    column_sortable_list = [VehicleType.sort_order]
    
    form_columns = [VehicleType.name, VehicleType.slug, VehicleType.icon, VehicleType.sort_order, VehicleType.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(VehicleTypeAdmin, VehicleType)


class BrandAdmin(ModelView, model=Brand):
    """Admin view for brands."""
    
    name = "Car Brand"
    name_plural = "Car Brands"
    icon = "fa-solid fa-award"
    
    column_list = [
        Brand.id, Brand.name, Brand.slug, Brand.country,
        Brand.is_popular, Brand.is_active, Brand.sort_order
    ]
    column_searchable_list = [Brand.name, Brand.slug, Brand.country]
    column_sortable_list = [Brand.name, Brand.sort_order]
    column_filters = [Brand.vehicle_type_id, Brand.is_popular, Brand.is_active]
    
    form_columns = [
        Brand.vehicle_type_id, Brand.name, Brand.slug, Brand.country,
        Brand.logo_url, Brand.is_popular, Brand.is_active, Brand.sort_order
    ]
    
    # Configure dropdown for vehicle_type_id
    form_ajax_refs = {
        "vehicle_type": {
            "fields": ("name",),
            "order_by": "name",
        }
    }
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(BrandAdmin, Brand)


class ModelAdmin(ModelView, model=Model):
    """Admin view for models."""
    
    name = "Car Model"
    name_plural = "Car Models"
    icon = "fa-solid fa-car-side"
    
    column_list = [
        Model.id, Model.name, Model.slug, Model.brand_id,
        Model.is_popular, Model.is_active, Model.sort_order
    ]
    column_searchable_list = [Model.name, Model.slug]
    column_sortable_list = [Model.name, Model.sort_order]
    column_filters = [Model.brand_id, Model.is_popular, Model.is_active]
    
    form_columns = [
        Model.brand_id, Model.name, Model.slug,
        Model.is_popular, Model.is_active, Model.sort_order
    ]
    
    # Configure dropdown for brand_id
    form_ajax_refs = {
        "brand": {
            "fields": ("name",),
            "order_by": "name",
        }
    }
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(ModelAdmin, Model)


class GenerationAdmin(ModelView, model=Generation):
    """Admin view for generations."""
    
    name = "Model Generation"
    name_plural = "Model Generations"
    icon = "fa-solid fa-timeline"
    
    column_list = [
        Generation.id, Generation.name, Generation.slug, Generation.model_id,
        Generation.year_start, Generation.year_end, Generation.is_active
    ]
    column_searchable_list = [Generation.name, Generation.slug]
    column_filters = [Generation.model_id, Generation.is_active]
    
    form_columns = [
        Generation.model_id, Generation.name, Generation.slug,
        Generation.year_start, Generation.year_end, Generation.image_url,
        Generation.sort_order, Generation.is_active
    ]
    
    # Configure dropdown for model_id
    form_ajax_refs = {
        "model": {
            "fields": ("name",),
            "order_by": "name",
        }
    }
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(GenerationAdmin, Generation)


class ModificationAdmin(ModelView, model=Modification):
    """Admin view for modifications."""
    
    name = "Car Modification"
    name_plural = "Car Modifications"
    icon = "fa-solid fa-gears"
    
    column_list = [
        Modification.id, Modification.name, Modification.generation_id,
        Modification.engine_volume, Modification.engine_power_hp, Modification.is_active
    ]
    column_searchable_list = [Modification.name]
    column_filters = [Modification.generation_id, Modification.fuel_type_id, Modification.is_active]
    
    form_columns = [
        Modification.generation_id, Modification.name, Modification.slug,
        Modification.engine_volume, Modification.engine_power_hp,
        Modification.engine_power_kw, Modification.fuel_type_id,
        Modification.transmission_id, Modification.drive_type_id,
        Modification.is_active
    ]
    
    # Configure dropdowns for foreign keys
    form_ajax_refs = {
        "generation": {
            "fields": ("name",),
            "order_by": "name",
        },
        "fuel_type": {
            "fields": ("name",),
            "order_by": "name",
        },
        "transmission": {
            "fields": ("name",),
            "order_by": "name",
        },
        "drive_type": {
            "fields": ("name",),
            "order_by": "name",
        }
    }
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(ModificationAdmin, Modification)


class BodyTypeAdmin(ModelView, model=BodyType):
    """Admin view for body types."""
    
    name = "Vehicle Body Type"
    name_plural = "Vehicle Body Types"
    icon = "fa-solid fa-car"
    
    column_list = [BodyType.id, BodyType.name, BodyType.slug, BodyType.is_active, BodyType.sort_order]
    column_searchable_list = [BodyType.name, BodyType.slug]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(BodyTypeAdmin, BodyType)


class TransmissionAdmin(ModelView, model=Transmission):
    """Admin view for transmissions."""
    
    name = "Transmission Type"
    name_plural = "Transmission Types"
    icon = "fa-solid fa-gears"
    
    column_list = [Transmission.id, Transmission.name, Transmission.short_name, Transmission.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(TransmissionAdmin, Transmission)


class FuelTypeAdmin(ModelView, model=FuelType):
    """Admin view for fuel types."""
    
    name = "Fuel Type"
    name_plural = "Fuel Types"
    icon = "fa-solid fa-gas-pump"
    
    column_list = [FuelType.id, FuelType.name, FuelType.slug, FuelType.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(FuelTypeAdmin, FuelType)


class DriveTypeAdmin(ModelView, model=DriveType):
    """Admin view for drive types."""
    
    name = "Drive Type"
    name_plural = "Drive Types"
    icon = "fa-solid fa-gear"
    
    column_list = [DriveType.id, DriveType.name, DriveType.slug, DriveType.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


class ColorAdmin(ModelView, model=Color):
    """Admin view for colors."""
    
    name = "Vehicle Color"
    name_plural = "Vehicle Colors"
    icon = "fa-solid fa-palette"
    
    column_list = [Color.id, Color.name, Color.slug, Color.hex_code, Color.is_active]
    column_searchable_list = [Color.name]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_vehicle_labels(DriveTypeAdmin, DriveType)
add_vehicle_labels(ColorAdmin, Color)


# ============ Locations ============

class CountryAdmin(ModelView, model=Country):
    """Admin view for countries."""
    
    name = "Country"
    name_plural = "Countries"
    icon = "fa-solid fa-globe"
    
    column_list = [Country.id, Country.name, Country.code, Country.flag_emoji, Country.is_active]
    column_searchable_list = [Country.name, Country.code]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_location_labels(CountryAdmin, Country)


class RegionAdmin(ModelView, model=Region):
    """Admin view for regions."""
    
    name = "Region"
    name_plural = "Regions"
    icon = "fa-solid fa-map"
    
    column_list = [Region.id, Region.name, Region.slug, Region.country_id, Region.is_active]
    column_searchable_list = [Region.name, Region.slug]
    column_filters = [Region.country_id, Region.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_location_labels(RegionAdmin, Region)


class CityAdmin(ModelView, model=City):
    """Admin view for cities."""
    
    name = "City"
    name_plural = "Cities"
    icon = "fa-solid fa-city"
    
    column_list = [
        City.id, City.name, City.slug, City.region_id,
        City.is_major, City.is_active
    ]
    column_searchable_list = [City.name, City.slug]
    column_filters = [City.region_id, City.is_major, City.is_active]
    
    can_create = True
    can_edit = True
    can_delete = True


# Apply labels
add_location_labels(CityAdmin, City)


# ============ Advertisements ============

class AdAdmin(ModelView, model=Ad):
    """Admin view for ads."""
    
    name = "Car Listing"
    name_plural = "Car Listings"
    icon = "fa-solid fa-rectangle-ad"
    
    column_list = [
        Ad.id, Ad.user_id, Ad.title, Ad.price, Ad.currency,
        Ad.year, Ad.status, Ad.published_at, Ad.created_at
    ]
    column_searchable_list = [Ad.title, Ad.description, Ad.vin]
    column_sortable_list = [Ad.id, Ad.price, Ad.year, Ad.created_at]
    column_filters = [Ad.status, Ad.category_id, Ad.brand_id, Ad.city_id]
    column_default_sort = [(Ad.created_at, True)]
    
    form_columns = [
        Ad.user_id, Ad.status, Ad.category_id, Ad.vehicle_type_id,
        Ad.brand_id, Ad.model_id, Ad.generation_id, Ad.modification_id,
        Ad.title, Ad.description, Ad.price, Ad.currency, Ad.year,
        Ad.mileage, Ad.vin, Ad.is_featured, Ad.is_top, Ad.is_urgent
    ]
    
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True


# Apply labels
add_ad_labels(AdAdmin)


class AdImageAdmin(ModelView, model=AdImage):
    """Admin view for ad images."""
    
    name = "Listing Image"
    name_plural = "Listing Images"
    icon = "fa-solid fa-image"
    
    column_list = [AdImage.id, AdImage.ad_id, AdImage.url, AdImage.sort_order, AdImage.created_at]
    column_filters = [AdImage.ad_id]
    column_sortable_list = [AdImage.ad_id, AdImage.sort_order, AdImage.created_at]
    
    can_create = False
    can_edit = True
    can_delete = True


# Apply labels
add_ad_media_labels(AdImageAdmin, AdImage)


class AdVideoAdmin(ModelView, model=AdVideo):
    """Admin view for ad videos."""
    
    name = "Listing Video"
    name_plural = "Listing Videos"
    icon = "fa-solid fa-video"
    
    column_list = [AdVideo.id, AdVideo.ad_id, AdVideo.url, AdVideo.created_at]
    column_filters = [AdVideo.ad_id]
    
    can_create = False
    can_edit = True
    can_delete = True


# Apply labels
add_ad_media_labels(AdVideoAdmin, AdVideo)


# ============ Chat ============

class DialogAdmin(ModelView, model=Dialog):
    """Admin view for dialogs."""
    
    name = "Chat Conversation"
    name_plural = "Chat Conversations"
    icon = "fa-solid fa-comments"
    
    column_list = [
        Dialog.id, Dialog.ad_id, Dialog.seller_id, Dialog.buyer_id,
        Dialog.last_message_at, Dialog.created_at
    ]
    column_filters = [Dialog.ad_id, Dialog.seller_id, Dialog.buyer_id]
    column_sortable_list = [Dialog.id, Dialog.last_message_at, Dialog.created_at]
    
    can_create = False
    can_edit = False
    can_delete = True


# Apply labels
add_chat_labels(DialogAdmin, Dialog)


class MessageAdmin(ModelView, model=Message):
    """Admin view for messages."""
    
    name = "Chat Message"
    name_plural = "Chat Messages"
    icon = "fa-solid fa-message"
    
    column_list = [
        Message.id, Message.dialog_id, Message.sender_id,
        Message.text, Message.is_read, Message.created_at
    ]
    column_searchable_list = [Message.text]
    column_filters = [Message.dialog_id, Message.sender_id, Message.is_read]
    column_sortable_list = [Message.id, Message.created_at]
    
    # Show only first 100 chars of text in list
    column_formatters = {
        Message.text: lambda m, a: (m.text[:100] + '...') if m.text and len(m.text) > 100 else m.text
    }
    
    can_create = False
    can_edit = False
    can_delete = True


# Apply labels
add_chat_labels(MessageAdmin, Message)


# ============ Moderation ============

class ReportAdmin(ModelView, model=Report):
    """Admin view for reports."""
    
    name = "User Report"
    name_plural = "User Reports"
    icon = "fa-solid fa-flag"
    
    column_list = [
        Report.id, Report.reporter_id, Report.report_type, Report.target_id,
        Report.reason, Report.status, Report.created_at
    ]
    column_filters = [Report.status, Report.reason, Report.report_type]
    column_sortable_list = [Report.id, Report.created_at]
    column_default_sort = [(Report.created_at, True)]
    
    column_searchable_list = [Report.description]
    
    form_columns = [
        Report.report_type, Report.target_id, Report.reason,
        Report.description, Report.status, Report.resolution_note
    ]
    
    can_create = False
    can_edit = True
    can_delete = True


# Apply labels
add_moderation_labels(ReportAdmin, Report)


class ModerationLogAdmin(ModelView, model=ModerationLog):
    """Admin view for moderation logs (System Activity Logs)."""
    
    name = "Activity Log"
    name_plural = "Activity Logs"
    icon = "fa-solid fa-clipboard-list"
    
    column_list = [
        ModerationLog.id, ModerationLog.moderator_id, ModerationLog.action,
        ModerationLog.target_type, ModerationLog.target_id, ModerationLog.created_at
    ]
    column_filters = [ModerationLog.action, ModerationLog.moderator_id, ModerationLog.target_type]
    column_sortable_list = [ModerationLog.id, ModerationLog.created_at]
    column_default_sort = [(ModerationLog.created_at, True)]
    
    column_searchable_list = [ModerationLog.reason, ModerationLog.details]
    
    column_details_list = [
        ModerationLog.id, ModerationLog.moderator_id, ModerationLog.action,
        ModerationLog.target_type, ModerationLog.target_id, ModerationLog.reason,
        ModerationLog.details, ModerationLog.report_id, ModerationLog.created_at
    ]
    
    can_create = False
    can_edit = False
    can_delete = False
    can_view_details = True


# Apply labels
add_moderation_labels(ModerationLogAdmin, ModerationLog)


# ============ Banners ============

class BannerAdmin(ModelView, model=Banner):
    """Admin view for banners."""
    
    name = "Promotional Banner"
    name_plural = "Promotional Banners"
    icon = "fa-solid fa-rectangle-ad"
    
    column_list = [
        Banner.id, Banner.title, Banner.banner_type, Banner.status,
        Banner.start_date, Banner.end_date, Banner.sort_order,
        Banner.impressions, Banner.clicks
    ]
    column_searchable_list = [Banner.title, Banner.description]
    column_sortable_list = [Banner.id, Banner.title, Banner.sort_order, Banner.start_date]
    column_filters = [Banner.banner_type, Banner.status]
    column_default_sort = [(Banner.sort_order, False)]
    
    form_columns = [
        Banner.title, Banner.description, Banner.banner_type,
        Banner.image_url, Banner.link_url, Banner.status,
        Banner.start_date, Banner.end_date, Banner.sort_order,
        Banner.target_pages
    ]
    
    column_details_list = [
        Banner.id, Banner.title, Banner.description, Banner.banner_type,
        Banner.image_url, Banner.link_url, Banner.status,
        Banner.start_date, Banner.end_date, Banner.sort_order,
        Banner.impressions, Banner.clicks, Banner.target_pages,
        Banner.created_at, Banner.updated_at
    ]
    
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True


# Apply labels
add_banner_labels(BannerAdmin)


# ============ Initialize Admin ============

def create_admin(app) -> Admin:
    """
    Create and configure admin panel.
    
    Args:
        app: FastAPI application instance
    
    Returns:
        Admin instance
    """
    from app.core.config import settings
    authentication_backend = AdminAuth(secret_key=settings.SECRET_KEY)
    
    admin = Admin(
        app=app,
        engine=engine,
        title="MillionAvto Admin",
        base_url="/admin",
        authentication_backend=authentication_backend,
        logo_url="/static/logo.png",
        templates_dir="app/templates/admin",
    )
    
    # User Management
    admin.add_view(UserAdmin)
    admin.add_view(UserSessionAdmin)
    
    # Categories
    admin.add_view(CategoryAdmin)
    
    # Vehicle References
    admin.add_view(VehicleTypeAdmin)
    admin.add_view(BrandAdmin)
    admin.add_view(ModelAdmin)
    admin.add_view(GenerationAdmin)
    admin.add_view(ModificationAdmin)
    admin.add_view(BodyTypeAdmin)
    admin.add_view(TransmissionAdmin)
    admin.add_view(FuelTypeAdmin)
    admin.add_view(DriveTypeAdmin)
    admin.add_view(ColorAdmin)
    
    # Locations
    admin.add_view(CountryAdmin)
    admin.add_view(RegionAdmin)
    admin.add_view(CityAdmin)
    
    # Advertisements
    admin.add_view(AdAdmin)
    admin.add_view(AdImageAdmin)
    admin.add_view(AdVideoAdmin)
    
    # Chat
    admin.add_view(DialogAdmin)
    admin.add_view(MessageAdmin)
    
    # Moderation
    admin.add_view(ReportAdmin)
    admin.add_view(ModerationLogAdmin)
    
    # Banners
    admin.add_view(BannerAdmin)
    
    return admin

