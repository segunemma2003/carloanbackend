"""
Banner API endpoints.
"""

from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func, update, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_current_user, require_admin
from app.models.user import User
from app.models.banner import Banner, BannerType, BannerStatus
from app.schemas.banner import (
    BannerResponse,
    BannerCreate,
    BannerUpdate,
    BannerListResponse,
)

router = APIRouter()


@router.get("/", response_model=BannerListResponse)
async def get_active_banners(
    banner_type: Optional[BannerType] = Query(None, description="Filter by banner type"),
    page: Optional[str] = Query(None, description="Target page"),
    db: AsyncSession = Depends(get_db),
) -> BannerListResponse:
    """
    Get active banners (public endpoint).
    Returns only active banners within their date range.
    """
    now = datetime.now(timezone.utc)
    
    query = select(Banner).where(
        Banner.status == BannerStatus.ACTIVE,
        or_(
            Banner.start_date.is_(None),
            Banner.start_date <= now
        ),
        or_(
            Banner.end_date.is_(None),
            Banner.end_date >= now
        )
    )
    
    if banner_type:
        query = query.where(Banner.banner_type == banner_type)
    
    # Sort by priority
    query = query.order_by(Banner.sort_order.desc(), Banner.created_at.desc())
    
    result = await db.execute(query)
    banners = result.scalars().all()
    
    return BannerListResponse(
        items=[BannerResponse.model_validate(banner) for banner in banners],
        total=len(banners)
    )


@router.get("/{banner_id}", response_model=BannerResponse)
async def get_banner(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
) -> BannerResponse:
    """
    Get banner details by ID (public endpoint).
    Returns banner if it's active and within date range.
    """
    now = datetime.now(timezone.utc)
    
    result = await db.execute(
        select(Banner).where(
            Banner.id == banner_id,
            Banner.status == BannerStatus.ACTIVE,
            or_(
                Banner.start_date.is_(None),
                Banner.start_date <= now
            ),
            or_(
                Banner.end_date.is_(None),
                Banner.end_date >= now
            )
        )
    )
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found or not active"
        )
    
    return BannerResponse.model_validate(banner)


@router.post("/{banner_id}/impression", status_code=status.HTTP_204_NO_CONTENT)
async def track_impression(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Track banner impression (view)."""
    await db.execute(
        update(Banner)
        .where(Banner.id == banner_id)
        .values(impressions=Banner.impressions + 1)
    )
    await db.commit()


@router.post("/{banner_id}/click", status_code=status.HTTP_204_NO_CONTENT)
async def track_click(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Track banner click."""
    await db.execute(
        update(Banner)
        .where(Banner.id == banner_id)
        .values(clicks=Banner.clicks + 1)
    )
    await db.commit()


# Admin endpoints

@router.get("/admin/all", response_model=BannerListResponse, dependencies=[Depends(require_admin)])
async def get_all_banners_admin(
    status_filter: Optional[BannerStatus] = None,
    banner_type: Optional[BannerType] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BannerListResponse:
    """
    Get all banners (admin only).
    Includes drafts, paused, and expired banners.
    """
    query = select(Banner)
    
    if status_filter:
        query = query.where(Banner.status == status_filter)
    
    if banner_type:
        query = query.where(Banner.banner_type == banner_type)
    
    # Get total count
    count_query = select(func.count()).select_from(Banner)
    if status_filter:
        count_query = count_query.where(Banner.status == status_filter)
    if banner_type:
        count_query = count_query.where(Banner.banner_type == banner_type)
    
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()
    
    # Get paginated results
    query = query.order_by(Banner.sort_order.desc(), Banner.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    banners = result.scalars().all()
    
    return BannerListResponse(
        items=[BannerResponse.model_validate(banner) for banner in banners],
        total=total,
        skip=skip,
        limit=limit
    )


@router.post("/admin/", response_model=BannerResponse, dependencies=[Depends(require_admin)])
async def create_banner_admin(
    banner_data: BannerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BannerResponse:
    """Create a new banner (admin only)."""
    banner = Banner(**banner_data.model_dump())
    
    db.add(banner)
    await db.commit()
    await db.refresh(banner)
    
    return BannerResponse.model_validate(banner)


@router.put("/admin/{banner_id}", response_model=BannerResponse, dependencies=[Depends(require_admin)])
async def update_banner_admin(
    banner_id: int,
    banner_data: BannerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BannerResponse:
    """Update a banner (admin only)."""
    result = await db.execute(
        select(Banner).where(Banner.id == banner_id)
    )
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    # Update fields
    update_data = banner_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(banner, field, value)
    
    await db.commit()
    await db.refresh(banner)
    
    return BannerResponse.model_validate(banner)


@router.delete("/admin/{banner_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin)])
async def delete_banner_admin(
    banner_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a banner (admin only)."""
    result = await db.execute(
        select(Banner).where(Banner.id == banner_id)
    )
    banner = result.scalar_one_or_none()
    
    if not banner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Banner not found"
        )
    
    await db.delete(banner)
    await db.commit()

