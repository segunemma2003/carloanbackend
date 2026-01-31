"""
Helper functions to add user-friendly labels to admin views.
"""

from sqladmin import ModelView
from app.models.user import User, UserSession
from app.models.category import Category
from app.models.vehicle import (
    VehicleType, Brand, Model, Generation, Modification,
    BodyType, Transmission, FuelType, DriveType, Color
)
from app.models.location import Country, Region, City
from app.models.ad import Ad, AdImage, AdVideo
from app.models.chat import Dialog, Message
from app.models.moderation import Report, ModerationLog
from app.models.banner import Banner


def add_user_labels(admin_view: ModelView):
    """Add user-friendly labels to UserAdmin."""
    admin_view.column_labels = {
        User.id: "ID",
        User.email: "Email Address",
        User.name: "Full Name",
        User.phone: "Phone Number",
        User.role: "User Role",
        User.account_type: "Account Type",
        User.company_name: "Company Name",
        User.company_description: "Company Description",
        User.company_website: "Company Website",
        User.company_logo_url: "Company Logo",
        User.company_address: "Company Address",
        User.email_verified: "Email Verified",
        User.phone_verified: "Phone Verified",
        User.is_active: "Account Active",
        User.is_blocked: "Account Blocked",
        User.blocked_reason: "Block Reason",
        User.city_id: "City",
        User.created_at: "Registration Date",
        User.updated_at: "Last Updated",
        User.last_login_at: "Last Login",
        User.last_seen_at: "Last Seen",
    }


def add_session_labels(admin_view: ModelView):
    """Add user-friendly labels to UserSessionAdmin."""
    admin_view.column_labels = {
        UserSession.id: "Session ID",
        UserSession.user_id: "User",
        UserSession.ip_address: "IP Address",
        UserSession.user_agent: "Device/Browser",
        UserSession.revoked: "Revoked",
        UserSession.created_at: "Created",
        UserSession.last_used_at: "Last Used",
        UserSession.expires_at: "Expires At",
    }


def add_category_labels(admin_view: ModelView):
    """Add user-friendly labels to CategoryAdmin."""
    admin_view.column_labels = {
        Category.id: "ID",
        Category.name: "Category Name",
        Category.slug: "URL Slug",
        Category.parent_id: "Parent Category",
        Category.level: "Level",
        Category.icon: "Icon",
        Category.image_url: "Category Image",
        Category.description: "Description",
        Category.seo_title: "SEO Title",
        Category.seo_description: "SEO Description",
        Category.seo_h1: "SEO Heading",
        Category.seo_text: "SEO Text",
        Category.is_active: "Active",
        Category.show_in_menu: "Show in Menu",
        Category.sort_order: "Display Order",
        Category.created_at: "Created",
    }


def add_vehicle_labels(admin_view: ModelView, model_class):
    """Add user-friendly labels to vehicle reference admin views."""
    if model_class == VehicleType:
        admin_view.column_labels = {
            VehicleType.id: "ID",
            VehicleType.name: "Vehicle Type",
            VehicleType.slug: "URL Slug",
            VehicleType.icon: "Icon",
            VehicleType.is_active: "Active",
            VehicleType.sort_order: "Display Order",
        }
    elif model_class == Brand:
        admin_view.column_labels = {
            Brand.id: "ID",
            Brand.vehicle_type_id: "Vehicle Type",
            Brand.name: "Brand Name",
            Brand.slug: "URL Slug",
            Brand.country: "Country",
            Brand.logo_url: "Brand Logo",
            Brand.is_popular: "Popular",
            Brand.is_active: "Active",
            Brand.sort_order: "Display Order",
        }
    elif model_class == Model:
        admin_view.column_labels = {
            Model.id: "ID",
            Model.brand_id: "Brand",
            Model.name: "Model Name",
            Model.slug: "URL Slug",
            Model.is_popular: "Popular",
            Model.is_active: "Active",
            Model.sort_order: "Display Order",
        }
    elif model_class == Generation:
        admin_view.column_labels = {
            Generation.id: "ID",
            Generation.model_id: "Model",
            Generation.name: "Generation Name",
            Generation.slug: "URL Slug",
            Generation.year_start: "Year Start",
            Generation.year_end: "Year End",
            Generation.is_active: "Active",
        }
    elif model_class == Modification:
        admin_view.column_labels = {
            Modification.id: "ID",
            Modification.generation_id: "Generation",
            Modification.name: "Modification Name",
            Modification.slug: "URL Slug",
            Modification.engine_volume: "Engine Volume (L)",
            Modification.engine_power_hp: "Power (HP)",
            Modification.engine_power_kw: "Power (kW)",
            Modification.fuel_type_id: "Fuel Type",
            Modification.transmission_id: "Transmission",
            Modification.drive_type_id: "Drive Type",
            Modification.is_active: "Active",
        }
    elif model_class == BodyType:
        admin_view.column_labels = {
            BodyType.id: "ID",
            BodyType.name: "Body Type",
            BodyType.slug: "URL Slug",
            BodyType.is_active: "Active",
            BodyType.sort_order: "Display Order",
        }
    elif model_class == Transmission:
        admin_view.column_labels = {
            Transmission.id: "ID",
            Transmission.name: "Transmission Type",
            Transmission.short_name: "Short Name",
            Transmission.is_active: "Active",
        }
    elif model_class == FuelType:
        admin_view.column_labels = {
            FuelType.id: "ID",
            FuelType.name: "Fuel Type",
            FuelType.slug: "URL Slug",
            FuelType.is_active: "Active",
        }
    elif model_class == DriveType:
        admin_view.column_labels = {
            DriveType.id: "ID",
            DriveType.name: "Drive Type",
            DriveType.slug: "URL Slug",
            DriveType.is_active: "Active",
        }
    elif model_class == Color:
        admin_view.column_labels = {
            Color.id: "ID",
            Color.name: "Color Name",
            Color.slug: "URL Slug",
            Color.hex_code: "Color Code",
            Color.is_active: "Active",
        }


def add_location_labels(admin_view: ModelView, model_class):
    """Add user-friendly labels to location admin views."""
    if model_class == Country:
        admin_view.column_labels = {
            Country.id: "ID",
            Country.name: "Country Name",
            Country.code: "Country Code",
            Country.flag_emoji: "Flag",
            Country.is_active: "Active",
        }
    elif model_class == Region:
        admin_view.column_labels = {
            Region.id: "ID",
            Region.name: "Region Name",
            Region.slug: "URL Slug",
            Region.country_id: "Country",
            Region.is_active: "Active",
        }
    elif model_class == City:
        admin_view.column_labels = {
            City.id: "ID",
            City.name: "City Name",
            City.slug: "URL Slug",
            City.region_id: "Region",
            City.is_major: "Major City",
            City.is_active: "Active",
        }


def add_ad_labels(admin_view: ModelView):
    """Add user-friendly labels to AdAdmin."""
    admin_view.column_labels = {
        Ad.id: "Listing ID",
        Ad.user_id: "Seller",
        Ad.status: "Status",
        Ad.category_id: "Category",
        Ad.vehicle_type_id: "Vehicle Type",
        Ad.brand_id: "Brand",
        Ad.model_id: "Model",
        Ad.generation_id: "Generation",
        Ad.modification_id: "Modification",
        Ad.title: "Title",
        Ad.description: "Description",
        Ad.price: "Price",
        Ad.currency: "Currency",
        Ad.year: "Year",
        Ad.mileage: "Mileage (km)",
        Ad.vin: "VIN Number",
        Ad.body_type_id: "Body Type",
        Ad.transmission_id: "Transmission",
        Ad.fuel_type_id: "Fuel Type",
        Ad.drive_type_id: "Drive Type",
        Ad.color_id: "Color",
        Ad.city_id: "City",
        Ad.is_featured: "Featured",
        Ad.is_top: "Top Listing",
        Ad.is_urgent: "Urgent",
        Ad.published_at: "Published Date",
        Ad.created_at: "Created",
        Ad.updated_at: "Last Updated",
    }


def add_ad_media_labels(admin_view: ModelView, model_class):
    """Add user-friendly labels to AdImageAdmin and AdVideoAdmin."""
    if model_class == AdImage:
        admin_view.column_labels = {
            AdImage.id: "ID",
            AdImage.ad_id: "Listing",
            AdImage.url: "Image URL",
            AdImage.sort_order: "Display Order",
            AdImage.created_at: "Uploaded",
        }
    elif model_class == AdVideo:
        admin_view.column_labels = {
            AdVideo.id: "ID",
            AdVideo.ad_id: "Listing",
            AdVideo.url: "Video URL",
            AdVideo.created_at: "Uploaded",
        }


def add_chat_labels(admin_view: ModelView, model_class):
    """Add user-friendly labels to chat admin views."""
    if model_class == Dialog:
        admin_view.column_labels = {
            Dialog.id: "Conversation ID",
            Dialog.ad_id: "Listing",
            Dialog.seller_id: "Seller",
            Dialog.buyer_id: "Buyer",
            Dialog.last_message_at: "Last Message",
            Dialog.created_at: "Started",
        }
    elif model_class == Message:
        admin_view.column_labels = {
            Message.id: "Message ID",
            Message.dialog_id: "Conversation",
            Message.sender_id: "Sender",
            Message.text: "Message Text",
            Message.is_read: "Read",
            Message.created_at: "Sent",
        }


def add_moderation_labels(admin_view: ModelView, model_class):
    """Add user-friendly labels to moderation admin views."""
    if model_class == Report:
        admin_view.column_labels = {
            Report.id: "Report ID",
            Report.reporter_id: "Reporter",
            Report.report_type: "Report Type",
            Report.target_id: "Target ID",
            Report.reason: "Reason",
            Report.description: "Description",
            Report.status: "Status",
            Report.resolved_by: "Resolved By",
            Report.resolved_at: "Resolved Date",
            Report.resolution_note: "Resolution Note",
            Report.created_at: "Reported",
        }
    elif model_class == ModerationLog:
        admin_view.column_labels = {
            ModerationLog.id: "Log ID",
            ModerationLog.moderator_id: "Admin/Moderator",
            ModerationLog.action: "Action Type",
            ModerationLog.target_type: "Target Type",
            ModerationLog.target_id: "Target ID",
            ModerationLog.reason: "Reason",
            ModerationLog.details: "Details",
            ModerationLog.report_id: "Related Report",
            ModerationLog.created_at: "Timestamp",
        }


def add_banner_labels(admin_view: ModelView):
    """Add user-friendly labels to BannerAdmin."""
    admin_view.column_labels = {
        Banner.id: "ID",
        Banner.title: "Banner Title",
        Banner.description: "Description",
        Banner.banner_type: "Banner Type",
        Banner.image_url: "Banner Image",
        Banner.link_url: "Link URL",
        Banner.status: "Status",
        Banner.start_date: "Start Date",
        Banner.end_date: "End Date",
        Banner.sort_order: "Display Order",
        Banner.impressions: "Views",
        Banner.clicks: "Clicks",
        Banner.target_pages: "Target Pages",
        Banner.created_at: "Created",
        Banner.updated_at: "Last Updated",
    }

