"""
Admin Dashboard API endpoints.
Provides statistics and metrics for the admin panel.
"""

from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import require_admin
from app.models.user import User, UserRole, AccountType
from app.models.ad import Ad, AdStatus
from app.models.category import Category
from app.models.chat import Dialog, Message
from app.models.favorites import Favorite, Comparison, ViewHistory
from app.models.moderation import Report, ReportStatus
from app.models.banner import Banner
from app.models.location import City

router = APIRouter()


@router.get("/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get comprehensive dashboard statistics.
    Returns all metrics needed for the admin dashboard.
    """
    try:
        # Calculate date ranges
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)
        
        # ============ USER STATISTICS ============
        # Total users
        total_users_result = await db.execute(select(func.count(User.id)))
        total_users = total_users_result.scalar() or 0
        
        # Active users
        active_users_result = await db.execute(
            select(func.count(User.id)).where(User.is_active == True)
        )
        active_users = active_users_result.scalar() or 0
        
        # Dealers
        dealers_result = await db.execute(
            select(func.count(User.id)).where(User.role == UserRole.DEALER)
        )
        dealers = dealers_result.scalar() or 0
        
        # New users (last 7 days)
        new_users_week_result = await db.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= week_ago, User.created_at <= now)
            )
        )
        new_users_week = new_users_week_result.scalar() or 0
        
        # New users (last 30 days)
        new_users_month_result = await db.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= month_ago, User.created_at <= now)
            )
        )
        new_users_month = new_users_month_result.scalar() or 0
        
        # Users by role
        users_by_role = {}
        for role in UserRole:
            role_count_result = await db.execute(
                select(func.count(User.id)).where(User.role == role)
            )
            users_by_role[role.value] = role_count_result.scalar() or 0
        
        # ============ AD STATISTICS ============
        # Total ads
        total_ads_result = await db.execute(select(func.count(Ad.id)))
        total_ads = total_ads_result.scalar() or 0
        
        # Active ads
        active_ads_result = await db.execute(
            select(func.count(Ad.id)).where(Ad.status == AdStatus.ACTIVE)
        )
        active_ads = active_ads_result.scalar() or 0
        
        # Pending ads
        pending_ads_result = await db.execute(
            select(func.count(Ad.id)).where(Ad.status == AdStatus.PENDING)
        )
        pending_ads = pending_ads_result.scalar() or 0
        
        # Rejected ads
        rejected_ads_result = await db.execute(
            select(func.count(Ad.id)).where(Ad.status == AdStatus.REJECTED)
        )
        rejected_ads = rejected_ads_result.scalar() or 0
        
        # Draft ads
        draft_ads_result = await db.execute(
            select(func.count(Ad.id)).where(Ad.status == AdStatus.DRAFT)
        )
        draft_ads = draft_ads_result.scalar() or 0
        
        # New ads (last 7 days)
        new_ads_week_result = await db.execute(
            select(func.count(Ad.id)).where(
                and_(Ad.created_at >= week_ago, Ad.created_at <= now)
            )
        )
        new_ads_week = new_ads_week_result.scalar() or 0
        
        # New ads (last 30 days)
        new_ads_month_result = await db.execute(
            select(func.count(Ad.id)).where(
                and_(Ad.created_at >= month_ago, Ad.created_at <= now)
            )
        )
        new_ads_month = new_ads_month_result.scalar() or 0
        
        # Ads by status
        ads_by_status = {}
        for status in AdStatus:
            status_count_result = await db.execute(
                select(func.count(Ad.id)).where(Ad.status == status)
            )
            ads_by_status[status.value] = status_count_result.scalar() or 0
        
        # ============ CATEGORY STATISTICS ============
        total_categories_result = await db.execute(select(func.count(Category.id)))
        total_categories = total_categories_result.scalar() or 0
        
        # ============ CHAT STATISTICS ============
        total_dialogs_result = await db.execute(select(func.count(Dialog.id)))
        total_dialogs = total_dialogs_result.scalar() or 0
        
        total_messages_result = await db.execute(select(func.count(Message.id)))
        total_messages = total_messages_result.scalar() or 0
        
        # ============ FAVORITES & INTERACTIONS ============
        total_favorites_result = await db.execute(select(func.count(Favorite.id)))
        total_favorites = total_favorites_result.scalar() or 0
        
        total_comparisons_result = await db.execute(select(func.count(Comparison.id)))
        total_comparisons = total_comparisons_result.scalar() or 0
        
        total_views_result = await db.execute(select(func.count(ViewHistory.id)))
        total_views = total_views_result.scalar() or 0
        
        # ============ MODERATION STATISTICS ============
        total_reports_result = await db.execute(select(func.count(Report.id)))
        total_reports = total_reports_result.scalar() or 0
        
        # Pending reports
        pending_reports_result = await db.execute(
            select(func.count(Report.id)).where(Report.status == ReportStatus.PENDING)
        )
        pending_reports = pending_reports_result.scalar() or 0
        
        # ============ BANNER STATISTICS ============
        total_banners_result = await db.execute(select(func.count(Banner.id)))
        total_banners = total_banners_result.scalar() or 0
        
        active_banners_result = await db.execute(
            select(func.count(Banner.id)).where(Banner.is_active == True)
        )
        active_banners = active_banners_result.scalar() or 0
        
        # ============ LOCATION STATISTICS ============
        total_cities_result = await db.execute(select(func.count(City.id)))
        total_cities = total_cities_result.scalar() or 0
        
        # ============ RECENT ACTIVITY (Last 24 hours) ============
        day_ago = now - timedelta(days=1)
        
        recent_users_result = await db.execute(
            select(func.count(User.id)).where(
                and_(User.created_at >= day_ago, User.created_at <= now)
            )
        )
        recent_users = recent_users_result.scalar() or 0
        
        recent_ads_result = await db.execute(
            select(func.count(Ad.id)).where(
                and_(Ad.created_at >= day_ago, Ad.created_at <= now)
            )
        )
        recent_ads = recent_ads_result.scalar() or 0
        
        recent_messages_result = await db.execute(
            select(func.count(Message.id)).where(
                and_(Message.created_at >= day_ago, Message.created_at <= now)
            )
        )
        recent_messages = recent_messages_result.scalar() or 0
        
        # ============ COMPILE RESPONSE ============
        return {
            "users": {
                "total": total_users,
                "active": active_users,
                "dealers": dealers,
                "new_week": new_users_week,
                "new_month": new_users_month,
                "by_role": users_by_role,
            },
            "ads": {
                "total": total_ads,
                "active": active_ads,
                "pending": pending_ads,
                "rejected": rejected_ads,
                "draft": draft_ads,
                "new_week": new_ads_week,
                "new_month": new_ads_month,
                "by_status": ads_by_status,
            },
            "categories": {
                "total": total_categories,
            },
            "chat": {
                "dialogs": total_dialogs,
                "messages": total_messages,
            },
            "interactions": {
                "favorites": total_favorites,
                "comparisons": total_comparisons,
                "views": total_views,
            },
            "moderation": {
                "total_reports": total_reports,
                "pending_reports": pending_reports,
            },
            "banners": {
                "total": total_banners,
                "active": active_banners,
            },
            "locations": {
                "cities": total_cities,
            },
            "recent_activity": {
                "users_24h": recent_users,
                "ads_24h": recent_ads,
                "messages_24h": recent_messages,
            },
            "timestamp": now.isoformat(),
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching dashboard stats: {str(e)}"
        )

