"""
Banner schemas for API requests and responses.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, HttpUrl

from app.models.banner import BannerType, BannerStatus


class BannerBase(BaseModel):
    """Base banner schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    banner_type: BannerType = BannerType.SIDEBAR
    image_url: str = Field(..., min_length=1, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    status: BannerStatus = BannerStatus.DRAFT
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_order: int = Field(default=0, ge=0)
    target_pages: Optional[str] = Field(None, description="JSON array of target pages")


class BannerCreate(BannerBase):
    """Schema for creating a banner."""
    pass


class BannerUpdate(BaseModel):
    """Schema for updating a banner."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    banner_type: Optional[BannerType] = None
    image_url: Optional[str] = Field(None, min_length=1, max_length=500)
    link_url: Optional[str] = Field(None, max_length=500)
    status: Optional[BannerStatus] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sort_order: Optional[int] = Field(None, ge=0)
    target_pages: Optional[str] = None


class BannerResponse(BannerBase):
    """Schema for banner response."""
    id: int
    impressions: int
    clicks: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class BannerListResponse(BaseModel):
    """Schema for banner list response."""
    items: List[BannerResponse]
    total: int
    skip: Optional[int] = 0
    limit: Optional[int] = None

