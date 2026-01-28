"""
Favorites, comparison, and view history endpoints.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import NotFoundError, ConflictError
from app.models.favorites import Favorite, Comparison, ViewHistory
from app.models.ad import Ad, AdStatus
from app.models.user import User
from app.models.location import City, Region
from app.schemas.ad import AdListResponse
from app.schemas.common import PaginatedResponse, MessageOut
from app.api.deps import get_current_user


router = APIRouter()


# ============ Favorites ============

@router.get("/", response_model=PaginatedResponse[AdListResponse])
async def get_favorites(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's favorite ads.
    """
    query = select(Favorite).options(
        selectinload(Favorite.ad).selectinload(Ad.brand),
        selectinload(Favorite.ad).selectinload(Ad.model),
        selectinload(Favorite.ad).selectinload(Ad.generation),
        selectinload(Favorite.ad).selectinload(Ad.transmission),
        selectinload(Favorite.ad).selectinload(Ad.fuel_type),
        selectinload(Favorite.ad).selectinload(Ad.city).selectinload(City.region),
        selectinload(Favorite.ad).selectinload(Ad.images),
    ).where(
        Favorite.user_id == current_user.id,
    ).order_by(Favorite.created_at.desc())

    # Count total
    count_query = select(func.count()).select_from(
        select(Favorite).where(Favorite.user_id == current_user.id).subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    result = await db.execute(query.offset(offset).limit(page_size))
    favorites = result.scalars().all()

    items = []
    for fav in favorites:
        ad = fav.ad
        if ad.deleted_at or ad.status != AdStatus.ACTIVE:
            continue

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
            is_favorite=True,
        ))

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{ad_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_to_favorites(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add ad to favorites.
    """
    # Check ad exists
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    # Check if already favorited
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.ad_id == ad_id,
        )
    )
    if result.scalar_one_or_none():
        return MessageOut(message="Ad already in favorites")

    # Add to favorites
    favorite = Favorite(user_id=current_user.id, ad_id=ad_id)
    db.add(favorite)

    # Update ad favorites count
    ad.favorites_count += 1

    await db.commit()

    return MessageOut(message="Added to favorites")


@router.delete("/{ad_id}", response_model=MessageOut)
async def remove_from_favorites(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove ad from favorites.
    """
    result = await db.execute(
        select(Favorite).where(
            Favorite.user_id == current_user.id,
            Favorite.ad_id == ad_id,
        )
    )
    favorite = result.scalar_one_or_none()

    if not favorite:
        return MessageOut(message="Ad not in favorites")

    await db.delete(favorite)

    # Update ad favorites count
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id)
    )
    ad = result.scalar_one_or_none()
    if ad and ad.favorites_count > 0:
        ad.favorites_count -= 1

    await db.commit()

    return MessageOut(message="Removed from favorites")


# ============ Comparison ============

@router.get("/comparison", response_model=List[AdListResponse])
async def get_comparison_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's comparison list.
    Limited to 10 items.
    """
    result = await db.execute(
        select(Comparison).options(
            selectinload(Comparison.ad).selectinload(Ad.brand),
            selectinload(Comparison.ad).selectinload(Ad.model),
            selectinload(Comparison.ad).selectinload(Ad.generation),
            selectinload(Comparison.ad).selectinload(Ad.transmission),
            selectinload(Comparison.ad).selectinload(Ad.fuel_type),
            selectinload(Comparison.ad).selectinload(Ad.city).selectinload(City.region),
            selectinload(Comparison.ad).selectinload(Ad.images),
        ).where(
            Comparison.user_id == current_user.id,
        ).order_by(Comparison.created_at.desc()).limit(10)
    )
    comparisons = result.scalars().all()

    items = []
    for comp in comparisons:
        ad = comp.ad
        if ad.deleted_at or ad.status != AdStatus.ACTIVE:
            continue

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

    return items


@router.post("/comparison/{ad_id}", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def add_to_comparison(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Add ad to comparison.
    Limited to 10 items.
    """
    # Check ad exists
    result = await db.execute(
        select(Ad).where(Ad.id == ad_id, Ad.deleted_at.is_(None))
    )
    ad = result.scalar_one_or_none()

    if not ad:
        raise NotFoundError("Ad not found", "ad", ad_id)

    # Check if already in comparison
    result = await db.execute(
        select(Comparison).where(
            Comparison.user_id == current_user.id,
            Comparison.ad_id == ad_id,
        )
    )
    if result.scalar_one_or_none():
        return MessageOut(message="Ad already in comparison")

    # Check limit
    count_result = await db.execute(
        select(func.count()).select_from(
            select(Comparison).where(Comparison.user_id == current_user.id).subquery()
        )
    )
    count = count_result.scalar() or 0

    if count >= 10:
        raise ConflictError("Comparison list is full (max 10 items)")

    # Add to comparison
    comparison = Comparison(user_id=current_user.id, ad_id=ad_id)
    db.add(comparison)
    await db.commit()

    return MessageOut(message="Added to comparison")


@router.delete("/comparison/{ad_id}", response_model=MessageOut)
async def remove_from_comparison(
    ad_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Remove ad from comparison.
    """
    result = await db.execute(
        select(Comparison).where(
            Comparison.user_id == current_user.id,
            Comparison.ad_id == ad_id,
        )
    )
    comparison = result.scalar_one_or_none()

    if not comparison:
        return MessageOut(message="Ad not in comparison")

    await db.delete(comparison)
    await db.commit()

    return MessageOut(message="Removed from comparison")


@router.delete("/comparison", response_model=MessageOut)
async def clear_comparison(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear comparison list.
    """
    await db.execute(
        delete(Comparison).where(Comparison.user_id == current_user.id)
    )
    await db.commit()

    return MessageOut(message="Comparison list cleared")


# ============ View History ============

@router.get("/history", response_model=List[AdListResponse])
async def get_view_history(
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user's view history.
    Returns last N viewed ads.
    """
    # Get distinct ad_ids in order of last view
    result = await db.execute(
        select(ViewHistory.ad_id, func.max(ViewHistory.viewed_at).label("last_view"))
        .where(ViewHistory.user_id == current_user.id)
        .group_by(ViewHistory.ad_id)
        .order_by(func.max(ViewHistory.viewed_at).desc())
        .limit(limit)
    )
    ad_views = result.all()

    if not ad_views:
        return []

    ad_ids = [av.ad_id for av in ad_views]

    # Get ads with relations
    result = await db.execute(
        select(Ad).options(
            selectinload(Ad.brand),
            selectinload(Ad.model),
            selectinload(Ad.generation),
            selectinload(Ad.transmission),
            selectinload(Ad.fuel_type),
            selectinload(Ad.city).selectinload(City.region),
            selectinload(Ad.images),
        ).where(
            Ad.id.in_(ad_ids),
            Ad.deleted_at.is_(None),
            Ad.status == AdStatus.ACTIVE,
        )
    )
    ads = {ad.id: ad for ad in result.scalars().all()}

    # Get user's favorites
    fav_result = await db.execute(
        select(Favorite.ad_id).where(Favorite.user_id == current_user.id)
    )
    user_favorites = set(fav_result.scalars().all())

    # Build response in correct order
    items = []
    for av in ad_views:
        ad = ads.get(av.ad_id)
        if not ad:
            continue

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

    return items


@router.delete("/history", response_model=MessageOut)
async def clear_view_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Clear view history.
    """
    await db.execute(
        delete(ViewHistory).where(ViewHistory.user_id == current_user.id)
    )
    await db.commit()

    return MessageOut(message="View history cleared")

