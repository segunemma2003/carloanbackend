"""
Advertisement/Listing endpoints.
CRUD operations, search, filtering, and statistics.
"""

import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.core.exceptions import NotFoundError, AuthorizationError, ValidationError
from app.models.ad import Ad, AdStatus, AdImage, AdVideo
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.vehicle import Brand, Model, Generation
from app.models.location import City, Region
from app.models.favorites import Favorite, Comparison, ViewHistory
from app.schemas.ad import (
    AdCreate,
    AdUpdate,
    AdResponse,
    AdListResponse,
    AdSearchParams,
    AdModerationAction,
    AdStats,
    AdImageCreate,
)
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user, get_current_user_optional, get_current_verified_user, require_moderator


router = APIRouter()


async def get_ad_with_relations(db: AsyncSession, ad_id: int) -> Ad:
    """Load ad with all related data."""
    result = await db.execute(
        select(Ad).options(
            selectinload(Ad.user),
            selectinload(Ad.category),
            selectinload(Ad.vehicle_type),
            selectinload(Ad.brand),
            selectinload(Ad.model),
            selectinload(Ad.generation),
            selectinload(Ad.modification),
            selectinload(Ad.body_type),
            selectinload(Ad.transmission),
            selectinload(Ad.fuel_type),
            selectinload(Ad.drive_type),
            selectinload(Ad.color),
            selectinload(Ad.city).selectinload(City.region).selectinload(Region.country),
            selectinload(Ad.images),
            selectinload(Ad.videos),
        ).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


def build_search_query(params: AdSearchParams):
    """Build search query from parameters."""
    query = select(Ad).where(
        Ad.status == AdStatus.ACTIVE,
        Ad.deleted_at.is_(None),
    )

    # Text search
    if params.q:
        search_term = f"%{params.q}%"
        query = query.where(
            or_(
                Ad.title.ilike(search_term),
                Ad.description.ilike(search_term),
            )
        )

    # Category
    if params.category_id:
        query = query.where(Ad.category_id == params.category_id)

    # Vehicle filters
    if params.vehicle_type_id:
        query = query.where(Ad.vehicle_type_id == params.vehicle_type_id)

    if params.brand_id:
        query = query.where(Ad.brand_id == params.brand_id)
    elif params.brand_ids:
        query = query.where(Ad.brand_id.in_(params.brand_ids))

    if params.model_id:
        query = query.where(Ad.model_id == params.model_id)
    elif params.model_ids:
        query = query.where(Ad.model_id.in_(params.model_ids))

    if params.generation_id:
        query = query.where(Ad.generation_id == params.generation_id)

    # Price
    if params.price_from:
        query = query.where(Ad.price >= params.price_from)
    if params.price_to:
        query = query.where(Ad.price <= params.price_to)

    # Year
    if params.year_from:
        query = query.where(Ad.year >= params.year_from)
    if params.year_to:
        query = query.where(Ad.year <= params.year_to)

    # Mileage
    if params.mileage_from:
        query = query.where(Ad.mileage >= params.mileage_from)
    if params.mileage_to:
        query = query.where(Ad.mileage <= params.mileage_to)

    # Specs
    if params.body_type_id:
        query = query.where(Ad.body_type_id == params.body_type_id)
    elif params.body_type_ids:
        query = query.where(Ad.body_type_id.in_(params.body_type_ids))

    if params.transmission_id:
        query = query.where(Ad.transmission_id == params.transmission_id)
    elif params.transmission_ids:
        query = query.where(Ad.transmission_id.in_(params.transmission_ids))

    if params.fuel_type_id:
        query = query.where(Ad.fuel_type_id == params.fuel_type_id)
    elif params.fuel_type_ids:
        query = query.where(Ad.fuel_type_id.in_(params.fuel_type_ids))

    if params.drive_type_id:
        query = query.where(Ad.drive_type_id == params.drive_type_id)
    elif params.drive_type_ids:
        query = query.where(Ad.drive_type_id.in_(params.drive_type_ids))

    if params.color_id:
        query = query.where(Ad.color_id == params.color_id)
    elif params.color_ids:
        query = query.where(Ad.color_id.in_(params.color_ids))

    # Engine
    if params.engine_volume_from:
        query = query.where(Ad.engine_volume >= params.engine_volume_from)
    if params.engine_volume_to:
        query = query.where(Ad.engine_volume <= params.engine_volume_to)
    if params.engine_power_from:
        query = query.where(Ad.engine_power >= params.engine_power_from)
    if params.engine_power_to:
        query = query.where(Ad.engine_power <= params.engine_power_to)

    # Condition
    if params.condition:
        query = query.where(Ad.condition == params.condition)
    if params.is_damaged is not None:
        query = query.where(Ad.is_damaged == params.is_damaged)
    if params.steering_wheel:
        query = query.where(Ad.steering_wheel == params.steering_wheel)

    # Location
    if params.city_id:
        query = query.where(Ad.city_id == params.city_id)
    elif params.region_id:
        query = query.join(City).where(City.region_id == params.region_id)

    # Other filters
    if params.has_photo:
        query = query.where(Ad.images.any())
    if params.has_video:
        query = query.where(Ad.videos.any())
    if params.has_vin:
        query = query.where(Ad.vin.isnot(None))

    if params.dealer_only:
        query = query.join(User).where(User.role == UserRole.DEALER)
    elif params.private_only:
        query = query.join(User).where(User.role == UserRole.USER)

    return query


def apply_sorting(query, sort_by: str):
    """Apply sorting to query."""
    if sort_by == "date":
        return query.order_by(Ad.is_top.desc(), Ad.is_featured.desc(), Ad.published_at.desc())
    elif sort_by == "price_asc":
        return query.order_by(Ad.is_top.desc(), Ad.price.asc())
    elif sort_by == "price_desc":
        return query.order_by(Ad.is_top.desc(), Ad.price.desc())
    elif sort_by == "mileage":
        return query.order_by(Ad.is_top.desc(), Ad.mileage.asc())
    elif sort_by == "year":
        return query.order_by(Ad.is_top.desc(), Ad.year.desc())
    return query.order_by(Ad.published_at.desc())


# ============ Public Endpoints ============

@router.get("/", response_model=PaginatedResponse[AdListResponse])
async def list_ads(
    params: AdSearchParams = Depends(),
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),  # Optional - public endpoint
):
    """
    Search and list ads with filters.
    """
    # Build query
    query = build_search_query(params)
    query = apply_sorting(query, params.sort_by)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    offset = (params.page - 1) * params.page_size
    query = query.offset(offset).limit(params.page_size)

    # Load with relations for list view
    query = query.options(
        selectinload(Ad.brand),
        selectinload(Ad.model),
        selectinload(Ad.generation),
        selectinload(Ad.transmission),
        selectinload(Ad.fuel_type),
        selectinload(Ad.city).selectinload(City.region),
        selectinload(Ad.images),
    )

    result = await db.execute(query)
    ads = result.scalars().all()

    # Get user's favorites for marking
    user_favorites = set()
    if current_user:
        fav_result = await db.execute(
            select(Favorite.ad_id).where(Favorite.user_id == current_user.id)
        )
        user_favorites = set(fav_result.scalars().all())

    # Build response
    items = []
    for ad in ads:
        main_image = ad.images[0].url if ad.images else None
        items.append(AdListResponse(
            id=ad.id,
            status=ad.status,
            user_id=ad.user_id,
            title=ad.title,
            price=ad.price,
            currency=ad.currency,
            year=ad.year,
            mileage=ad.mileage,
            main_image_url=main_image,
            brand_name=ad.brand.name,
            model_name=ad.model.name,
            generation_name=ad.generation.name if ad.generation else None,
            engine_volume=ad.engine_volume,
            engine_power=ad.engine_power,
            transmission_name=ad.transmission.name if ad.transmission else None,
            fuel_type_name=ad.fuel_type.name if ad.fuel_type else None,
            city_name=ad.city.name,
            region_name=ad.city.region.name,
            published_at=ad.published_at,
            created_at=ad.created_at,
            views_count=ad.views_count,
            is_featured=ad.is_featured,
            is_top=ad.is_top,
            is_urgent=ad.is_urgent,
            is_favorite=ad.id in user_favorites,
        ))

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )


@router.get("/{ad_id}", response_model=AdResponse)
async def get_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),  # Optional - public endpoint
):
    """
    Get ad by ID with full details.
    """
    ad = await get_ad_with_relations(db, ad_id)
    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    # Only show active ads to non-owners
    if ad.status != AdStatus.ACTIVE:
        if not current_user or (current_user.id != ad.user_id and not current_user.is_moderator):
            raise NotFoundError("Ad not found", "ad", ad_id)

    # Increment view count
    ad.views_count += 1

    # Track view history for logged-in users
    if current_user and current_user.id != ad.user_id:
        view = ViewHistory(user_id=current_user.id, ad_id=ad_id)
        db.add(view)

    await db.commit()

    # Check if favorited/compared
    is_favorite = False
    is_in_comparison = False
    if current_user:
        fav_result = await db.execute(
            select(Favorite).where(
                Favorite.user_id == current_user.id,
                Favorite.ad_id == ad_id,
            )
        )
        is_favorite = fav_result.scalar_one_or_none() is not None

        comp_result = await db.execute(
            select(Comparison).where(
                Comparison.user_id == current_user.id,
                Comparison.ad_id == ad_id,
            )
        )
        is_in_comparison = comp_result.scalar_one_or_none() is not None

    response = AdResponse.model_validate(ad)
    response.is_favorite = is_favorite
    response.is_in_comparison = is_in_comparison

    return response


# ============ Authenticated Endpoints ============

@router.post("/", response_model=AdResponse, status_code=status.HTTP_201_CREATED)
async def create_ad(
    ad_data: AdCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_verified_user),
):
    """
    Create new ad.
    Requires verified email.
    """
    # Parse features if provided
    features_json = None
    if ad_data.features:
        features_json = json.dumps(ad_data.features)

    # Create ad
    ad = Ad(
        user_id=current_user.id,
        status=AdStatus.PENDING,  # Pending moderation
        category_id=ad_data.category_id,
        vehicle_type_id=ad_data.vehicle_type_id,
        brand_id=ad_data.brand_id,
        model_id=ad_data.model_id,
        generation_id=ad_data.generation_id,
        modification_id=ad_data.modification_id,
        year=ad_data.year,
        mileage=ad_data.mileage,
        body_type_id=ad_data.body_type_id,
        transmission_id=ad_data.transmission_id,
        fuel_type_id=ad_data.fuel_type_id,
        drive_type_id=ad_data.drive_type_id,
        color_id=ad_data.color_id,
        engine_volume=ad_data.engine_volume,
        engine_power=ad_data.engine_power,
        condition=ad_data.condition,
        is_damaged=ad_data.is_damaged,
        vin=ad_data.vin,
        pts_type=ad_data.pts_type,
        owners_count=ad_data.owners_count,
        steering_wheel=ad_data.steering_wheel,
        price=ad_data.price,
        currency=ad_data.currency,
        price_negotiable=ad_data.price_negotiable,
        exchange_possible=ad_data.exchange_possible,
        title=ad_data.title,
        description=ad_data.description,
        contact_name=ad_data.contact_name or current_user.name,
        contact_phone=ad_data.contact_phone or current_user.phone,
        show_phone=ad_data.show_phone,
        city_id=ad_data.city_id,
        address=ad_data.address,
        latitude=ad_data.latitude,
        longitude=ad_data.longitude,
        features=features_json,
    )
    db.add(ad)
    await db.flush()

    # Add images
    for i, img_data in enumerate(ad_data.images):
        image = AdImage(
            ad_id=ad.id,
            url=img_data.url,
            thumbnail_url=img_data.thumbnail_url,
            sort_order=img_data.sort_order or i,
            is_main=img_data.is_main or (i == 0),
        )
        db.add(image)

    # Add videos
    for i, vid_data in enumerate(ad_data.videos):
        video = AdVideo(
            ad_id=ad.id,
            url=vid_data.url,
            video_type=vid_data.video_type,
            thumbnail_url=vid_data.thumbnail_url,
            sort_order=i,
        )
        db.add(video)

    await db.commit()

    # Reload with relations
    ad = await get_ad_with_relations(db, ad.id)
    return AdResponse.model_validate(ad)


@router.patch("/{ad_id}", response_model=AdResponse)
async def update_ad(
    ad_id: int,
    update_data: AdUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update ad.
    Only owner can update their ads.
    """
    ad = await get_ad_with_relations(db, ad_id)
    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError("You can only edit your own ads")

    update_dict = update_data.model_dump(exclude_unset=True)

    # Handle features
    if "features" in update_dict:
        if update_dict["features"]:
            update_dict["features"] = json.dumps(update_dict["features"])
        else:
            update_dict["features"] = None

    for field, value in update_dict.items():
        setattr(ad, field, value)

    # Reset to pending if significant changes
    if ad.status == AdStatus.ACTIVE and any(
        field in update_dict for field in ["title", "description", "price", "vin"]
    ):
        ad.status = AdStatus.PENDING

    await db.commit()
    await db.refresh(ad)

    ad = await get_ad_with_relations(db, ad.id)
    return AdResponse.model_validate(ad)


@router.delete("/{ad_id}", response_model=MessageOut)
async def delete_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Soft delete ad.
    """
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError("You can only delete your own ads")

    ad.soft_delete()
    await db.commit()

    return MessageOut(message="Ad deleted successfully")


@router.post("/{ad_id}/archive", response_model=MessageOut)
async def archive_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Archive ad (mark as sold or inactive).
    """
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id:
        raise AuthorizationError("You can only archive your own ads")

    ad.status = AdStatus.ARCHIVED
    await db.commit()

    return MessageOut(message="Ad archived successfully")


@router.post("/{ad_id}/sold", response_model=MessageOut)
async def mark_as_sold(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark ad as sold.
    """
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id:
        raise AuthorizationError("You can only mark your own ads as sold")

    ad.status = AdStatus.SOLD
    await db.commit()

    return MessageOut(message="Ad marked as sold")


@router.post("/{ad_id}/republish", response_model=AdResponse)
async def republish_ad(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Republish archived/expired ad.
    """
    ad = await get_ad_with_relations(db, ad_id)

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id:
        raise AuthorizationError("You can only republish your own ads")

    if ad.status not in [AdStatus.ARCHIVED, AdStatus.EXPIRED, AdStatus.SOLD]:
        raise ValidationError("Only archived, expired, or sold ads can be republished")

    ad.status = AdStatus.PENDING  # Back to moderation
    await db.commit()
    await db.refresh(ad)

    return AdResponse.model_validate(ad)


@router.get("/{ad_id}/stats", response_model=AdStats)
async def get_ad_stats(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed statistics for an ad.
    Only owner can view stats.
    """
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.user_id != current_user.id and not current_user.is_admin:
        raise AuthorizationError("You can only view stats for your own ads")

    # Calculate period-based views
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)
    month_start = today_start - timedelta(days=30)

    # Count views per period
    views_today_result = await db.execute(
        select(func.count(ViewHistory.id)).where(
            ViewHistory.ad_id == ad_id,
            ViewHistory.viewed_at >= today_start,
        )
    )
    views_today = views_today_result.scalar() or 0

    views_week_result = await db.execute(
        select(func.count(ViewHistory.id)).where(
            ViewHistory.ad_id == ad_id,
            ViewHistory.viewed_at >= week_start,
        )
    )
    views_week = views_week_result.scalar() or 0

    views_month_result = await db.execute(
        select(func.count(ViewHistory.id)).where(
            ViewHistory.ad_id == ad_id,
            ViewHistory.viewed_at >= month_start,
        )
    )
    views_month = views_month_result.scalar() or 0

    return AdStats(
        views_count=ad.views_count,
        favorites_count=ad.favorites_count,
        messages_count=ad.messages_count,
        phone_views_count=ad.phone_views_count,
        views_today=views_today,
        views_week=views_week,
        views_month=views_month,
    )


# ============ User's Ads ============

@router.get("/my/ads", response_model=PaginatedResponse[AdListResponse])
async def get_my_ads(
    status_filter: Optional[AdStatus] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current user's ads.
    """
    query = select(Ad).where(
        Ad.user_id == current_user.id,
        Ad.deleted_at.is_(None),
    )

    if status_filter:
        query = query.where(Ad.status == status_filter)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size).order_by(Ad.created_at.desc())

    query = query.options(
        selectinload(Ad.brand),
        selectinload(Ad.model),
        selectinload(Ad.city).selectinload(City.region),
        selectinload(Ad.images),
    )

    result = await db.execute(query)
    ads = result.scalars().all()

    items = []
    for ad in ads:
        main_image = ad.images[0].url if ad.images else None
        items.append(AdListResponse(
            id=ad.id,
            status=ad.status,
            user_id=ad.user_id,
            title=ad.title,
            price=ad.price,
            currency=ad.currency,
            year=ad.year,
            mileage=ad.mileage,
            main_image_url=main_image,
            brand_name=ad.brand.name,
            model_name=ad.model.name,
            generation_name=ad.generation.name if ad.generation else None,
            engine_volume=ad.engine_volume,
            engine_power=ad.engine_power,
            transmission_name=ad.transmission.name if ad.transmission else None,
            fuel_type_name=ad.fuel_type.name if ad.fuel_type else None,
            city_name=ad.city.name,
            region_name=ad.city.region.name,
            published_at=ad.published_at,
            created_at=ad.created_at,
            views_count=ad.views_count,
            is_featured=ad.is_featured,
            is_top=ad.is_top,
            is_urgent=ad.is_urgent,
            is_favorite=False,
        ))

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


# ============ Moderation ============

@router.get("/moderation/pending", response_model=PaginatedResponse[AdListResponse])
async def get_pending_ads(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Get ads pending moderation (moderator only).
    """
    query = select(Ad).where(
        Ad.status == AdStatus.PENDING,
        Ad.deleted_at.is_(None),
    ).order_by(Ad.created_at.asc())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    query = query.options(
        selectinload(Ad.brand),
        selectinload(Ad.model),
        selectinload(Ad.city).selectinload(City.region),
        selectinload(Ad.images),
    )

    result = await db.execute(query)
    ads = result.scalars().all()

    items = []
    for ad in ads:
        main_image = ad.images[0].url if ad.images else None
        items.append(AdListResponse(
            id=ad.id,
            status=ad.status,
            user_id=ad.user_id,
            title=ad.title,
            price=ad.price,
            currency=ad.currency,
            year=ad.year,
            mileage=ad.mileage,
            main_image_url=main_image,
            brand_name=ad.brand.name,
            model_name=ad.model.name,
            generation_name=ad.generation.name if ad.generation else None,
            engine_volume=ad.engine_volume,
            engine_power=ad.engine_power,
            transmission_name=None,
            fuel_type_name=None,
            city_name=ad.city.name,
            region_name=ad.city.region.name,
            published_at=ad.published_at,
            created_at=ad.created_at,
            views_count=ad.views_count,
            is_featured=ad.is_featured,
            is_top=ad.is_top,
            is_urgent=ad.is_urgent,
            is_favorite=False,
        ))

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{ad_id}/moderate", response_model=AdResponse)
async def moderate_ad(
    ad_id: int,
    action: AdModerationAction,
    db: AsyncSession = Depends(get_db),
    moderator: User = Depends(require_moderator),
):
    """
    Approve or reject ad (moderator only).
    """
    ad = await get_ad_with_relations(db, ad_id)

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    if ad.status != AdStatus.PENDING:
        raise ValidationError("Ad is not pending moderation")

    now = datetime.now(timezone.utc)

    if action.action == "approve":
        ad.status = AdStatus.ACTIVE
        ad.published_at = now
        ad.expires_at = now + timedelta(days=30)  # 30 days active
        ad.rejection_reason = None
    elif action.action == "reject":
        ad.status = AdStatus.REJECTED
        ad.rejection_reason = action.reason

    ad.moderated_at = now
    ad.moderated_by = moderator.id

    await db.commit()
    await db.refresh(ad)

    return AdResponse.model_validate(ad)

